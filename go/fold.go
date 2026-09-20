package protocol

import (
	"encoding/json"
	"sort"

	"github.com/nbd-wtf/go-nostr"
)

// FoldResult is the effective fact for one address (spec/envelope.md §3).
type FoldResult struct {
	Subject   string                 `json:"subject"`
	Revision  int                    `json:"revision"`
	Enabled   bool                   `json:"enabled"`
	Conflicts int                    `json:"conflicts"`
	Fact      map[string]interface{} `json:"fact"`
}

// Fold computes the effective fact over valid events for one kind.
func Fold(kind int, events []*nostr.Event) FoldResult {
	valid := make([]*nostr.Event, 0, len(events))
	for _, e := range events {
		if e == nil {
			continue
		}
		if Validate(e).Accept {
			valid = append(valid, e)
		}
	}
	if len(valid) == 0 {
		return FoldResult{Enabled: true}
	}

	sort.SliceStable(valid, func(i, j int) bool {
		a, b := revisionOf(valid[i]), revisionOf(valid[j])
		if a != b {
			return a < b
		}
		ca, cb := valid[i].CreatedAt, valid[j].CreatedAt
		if ca != cb {
			return ca < cb
		}
		return valid[i].ID < valid[j].ID
	})

	winner := valid[len(valid)-1]
	topRevision := revisionOf(winner)
	winnerKey := contentKey(winner)

	conflicts := 0
	for _, e := range valid {
		if declaresRevision(e) && revisionOf(e) == topRevision && contentKey(e) != winnerKey {
			conflicts++
		}
	}

	body, _ := parseContent(winner)
	d := tagValue(winner, "d")
	subject := ""
	if d != "" {
		subject = d
	} else if s, ok := body["subject"].(string); ok {
		subject = s
	}
	enabled := true
	if e, ok := body["enabled"]; ok {
		if b, ok := e.(bool); ok {
			enabled = b
		}
	}

	var fact map[string]interface{}
	switch kind {
	case KindCapability:
		fact = map[string]interface{}{
			"type":   firstString(body["type"]),
			"scopes": stringSlice(body["scopes"]),
		}
	case KindIdentityDefinition:
		fact = map[string]interface{}{
			"username":    firstString(body["username"]),
			"signer_type": firstString(body["signer_type"]),
		}
	case KindTrustPolicy:
		fact = map[string]interface{}{
			"schema": body["schema"],
			"value":  valueOrEmpty(body["value"]),
		}
	default:
		fact = map[string]interface{}{}
	}

	if conflicts < 0 {
		conflicts = 0
	}
	return FoldResult{
		Subject:   subject,
		Revision:  topRevision,
		Enabled:   enabled,
		Conflicts: conflicts,
		Fact:      fact,
	}
}

func revisionOf(event *nostr.Event) int {
	body, ok := parseContent(event)
	if ok {
		if r, ok := body["revision"]; ok {
			if n, ok := r.(float64); ok && n == float64(int64(n)) {
				return int(n)
			}
		}
	}
	return 0
}

func declaresRevision(event *nostr.Event) bool {
	body, ok := parseContent(event)
	if !ok {
		return false
	}
	_, present := body["revision"]
	return present
}

func contentKey(event *nostr.Event) string {
	body, ok := parseContent(event)
	if !ok {
		return ""
	}
	relevant := map[string]interface{}{}
	for k, v := range body {
		if k == "revision" || k == "updated_by" || k == "reason" {
			continue
		}
		relevant[k] = v
	}
	raw, err := json.Marshal(relevant)
	if err != nil {
		return ""
	}
	return string(raw)
}

func firstString(v interface{}) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func stringSlice(v interface{}) []string {
	out := []string{}
	if list, ok := v.([]interface{}); ok {
		for _, item := range list {
			if s, ok := item.(string); ok {
				out = append(out, s)
			}
		}
	}
	return out
}

func valueOrEmpty(v interface{}) interface{} {
	if v == nil {
		return map[string]interface{}{}
	}
	return v
}
