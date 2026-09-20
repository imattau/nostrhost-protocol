package protocol

import (
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/nbd-wtf/go-nostr"
)

// Verdict is a validation outcome plus a stable reason code (spec/envelope.md §2).
type Verdict struct {
	Accept bool
	Code   string
}

// EventModelError describes a schema validation failure for a custom kind.
// Compatible with the former eventmodel.EventModelError so the relay's existing
// error handling keeps working after the migration.
type EventModelError struct {
	Kind   int
	Reason string
}

func (e *EventModelError) Error() string {
	return fmt.Sprintf("invalid kind %d event: %s", e.Kind, e.Reason)
}

// AsEventModelError converts a Verdict into an EventModelError (or nil when
// accepted). The reason is the verdict code itself.
func (v Verdict) AsEventModelError(kind int) error {
	if v.Accept {
		return nil
	}
	return &EventModelError{Kind: kind, Reason: v.Code}
}

// Validate applies the event-protocol rules in order and returns the first
// failure. Non-custom / non-corpus kinds are accepted (the relay treats
// standard NIP kinds as opaque). The result codes for the corpus kinds match
// spec/envelope.md §2 exactly.
func Validate(event *nostr.Event) Verdict {
	if event == nil {
		return Verdict{Accept: false, Code: "content-not-json"}
	}
	kind := event.Kind
	body, contentOK := parseContent(event)

	if JSONContentKinds[kind] && !contentOK {
		return Verdict{Accept: false, Code: "content-not-json"}
	}

	d := tagValue(event, "d")
	if AddressableKinds[kind] {
		if d == "" {
			return Verdict{Accept: false, Code: "missing-d"}
		}
		if Hex64DKinds[kind] && !isHex64(d) {
			return Verdict{Accept: false, Code: "d-not-hex64"}
		}
	}

	if schema, ok := body["schema"]; ok {
		if n, ok := schema.(float64); !ok || n < 1 || n != float64(int64(n)) {
			return Verdict{Accept: false, Code: "schema-invalid"}
		}
	}
	if revision, ok := body["revision"]; ok {
		if n, ok := revision.(float64); !ok || n < 0 || n != float64(int64(n)) {
			return Verdict{Accept: false, Code: "revision-invalid"}
		}
	}
	if subject, ok := body["subject"]; ok && d != "" {
		if s, ok := subject.(string); !ok || s != d {
			return Verdict{Accept: false, Code: "subject-mismatch"}
		}
	}

	switch kind {
	case KindCapability:
		if t, ok := body["type"]; !ok {
			return Verdict{Accept: false, Code: "31100:missing-type"}
		} else if s, ok := t.(string); !ok || s == "" {
			return Verdict{Accept: false, Code: "31100:missing-type"}
		}
		if scopes, ok := body["scopes"]; ok {
			list, ok := scopes.([]interface{})
			if !ok {
				return Verdict{Accept: false, Code: "31100:scopes-not-array"}
			}
			for _, s := range list {
				if _, ok := s.(string); !ok {
					return Verdict{Accept: false, Code: "31100:scopes-not-array"}
				}
			}
		}
	case KindTrustPolicy:
		if _, ok := body["schema"]; !ok {
			return Verdict{Accept: false, Code: "31101:missing-schema"}
		}
	case KindIdentityDefinition:
		if enabled, ok := body["enabled"]; ok {
			if _, ok := enabled.(bool); !ok {
				return Verdict{Accept: false, Code: "31102:enabled-not-bool"}
			}
		} else {
			enabled = true
		}
		if admin, ok := body["admin"]; ok {
			if _, ok := admin.(bool); !ok {
				return Verdict{Accept: false, Code: "31102:admin-not-bool"}
			}
		}
		username, _ := body["username"].(string)
		if username == "" && body["enabled"] != false {
			return Verdict{Accept: false, Code: "31102:missing-username"}
		}
		signerType, _ := body["signer_type"].(string)
		if signerType != "" && !SignerTypes[signerType] {
			return Verdict{Accept: false, Code: "31102:bad-signer-type"}
		}
	case KindDelegation:
		p := tagValue(event, "p")
		server := tagValue(event, "server")
		expiry := tagValue(event, "expiry")
		if !isHex64(p) || !isHex64(server) {
			return Verdict{Accept: false, Code: "27236:bad-tags"}
		}
		if expiry == "" {
			return Verdict{Accept: false, Code: "27236:bad-expiry"}
		}
		if n, err := strconv.ParseInt(expiry, 10, 64); err != nil || n <= 0 {
			return Verdict{Accept: false, Code: "27236:bad-expiry"}
		}
		if len(tagsNamed(event, "scope")) == 0 {
			return Verdict{Accept: false, Code: "27236:missing-scope"}
		}
	case KindDelegationRevocation:
		e := tagValue(event, "e")
		if !isHex64(e) {
			return Verdict{Accept: false, Code: "27237:missing-e"}
		}
	case KindPermissionSet:
		for _, p := range tagsNamed(event, "p") {
			if len(p) < 2 || !isHex64(p[1]) {
				return Verdict{Accept: false, Code: "30000:bad-p"}
			}
		}
	case KindMuteList:
		for _, p := range tagsNamed(event, "p") {
			if len(p) < 2 || !isHex64(p[1]) {
				return Verdict{Accept: false, Code: "10000:bad-p"}
			}
		}
	case KindRelayList:
		relays := []string{}
		for _, r := range tagsNamed(event, "r") {
			if len(r) >= 2 {
				relays = append(relays, r[1])
			}
		}
		if len(relays) == 0 {
			return Verdict{Accept: false, Code: "10002:bad-r"}
		}
		for _, u := range relays {
			if !isWebSocketURL(u) {
				return Verdict{Accept: false, Code: "10002:bad-r"}
			}
		}
	case KindOperationRequest:
		var body2 struct {
			Tool string `json:"tool"`
		}
		if err := json.Unmarshal([]byte(event.Content), &body2); err != nil {
			return Verdict{Accept: false, Code: "content-not-json"}
		}
		if strings.TrimSpace(body2.Tool) == "" {
			return Verdict{Accept: false, Code: "operation-request-missing-tool"}
		}
	case KindOperationApproval, KindOperationRejection, KindExecutionStarted, KindExecutionResult, KindExecutionProgress:
		e := tagValue(event, "e")
		if e == "" {
			return Verdict{Accept: false, Code: "chain-step-missing-e"}
		}
		if !contentOK && event.Content != "" {
			return Verdict{Accept: false, Code: "content-not-json"}
		}
	case KindSystemEvent, KindServiceEvent, KindBackupEvent, KindSecurityEvent, KindStateBundle:
		if event.Content != "" && !contentOK {
			return Verdict{Accept: false, Code: "content-not-json"}
		}
	case KindBuildAttestation:
		if d == "" {
			return Verdict{Accept: false, Code: "missing-d"}
		}
		if event.Content != "" && !contentOK {
			return Verdict{Accept: false, Code: "content-not-json"}
		}
	}

	return Verdict{Accept: true}
}

// ValidateError returns an error for a rejected event (nil when accepted or
// non-custom). Compatible with the former eventmodel.Validate contract.
func ValidateError(event *nostr.Event) error {
	if event == nil || !IsCustomKind(event.Kind) {
		return nil
	}
	return Validate(event).AsEventModelError(event.Kind)
}

func parseContent(event *nostr.Event) (map[string]interface{}, bool) {
	if event.Content == "" {
		return map[string]interface{}{}, true
	}
	var body map[string]interface{}
	if err := json.Unmarshal([]byte(event.Content), &body); err != nil {
		return nil, false
	}
	return body, true
}

func tagValue(event *nostr.Event, name string) string {
	tag := event.Tags.Find(name)
	if tag == nil || len(tag) < 2 {
		return ""
	}
	return tag[1]
}

func tagsNamed(event *nostr.Event, name string) [][]string {
	out := [][]string{}
	for _, tag := range event.Tags {
		if len(tag) > 0 && tag[0] == name {
			out = append(out, tag)
		}
	}
	return out
}

func isHex64(s string) bool {
	if len(s) != 64 {
		return false
	}
	for _, c := range s {
		if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')) {
			return false
		}
	}
	return true
}

func isWebSocketURL(s string) bool {
	lower := strings.ToLower(s)
	return strings.HasPrefix(lower, "ws://") || strings.HasPrefix(lower, "wss://")
}

// ReasonCode maps an error (EventModelError) to the stable corpus vocabulary.
// Returns "schema-invalid" for unexpected reasons.
func ReasonCode(err error) string {
	var modelErr *EventModelError
	if !errors.As(err, &modelErr) {
		return "schema-invalid"
	}
	code := modelErr.Reason
	if code == "" {
		return "schema-invalid"
	}
	return code
}

// NoticeBody is the optional convention carried by system/service/backup/
// security notices: a free-form "class", a "severity" (SeverityInfo/Warning/
// Critical) and a human-readable "summary". All three are optional.
type NoticeBody struct {
	Class    string `json:"class"`
	Severity string `json:"severity"`
	Summary  string `json:"summary"`
}

// Notice extracts the class/severity/summary convention from a notice event.
// ok is false when the content is empty or not shaped like a notice body
// (callers should fall back to kind-derived defaults).
func Notice(event *nostr.Event) (class, severity, summary string, ok bool) {
	if event == nil || event.Content == "" {
		return "", "", "", false
	}
	var body NoticeBody
	if err := json.Unmarshal([]byte(event.Content), &body); err != nil {
		return "", "", "", false
	}
	return body.Class, body.Severity, body.Summary, true
}
