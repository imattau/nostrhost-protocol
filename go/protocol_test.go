package protocol

import (
	"encoding/json"
	"testing"

	"github.com/nbd-wtf/go-nostr"
)

// jsonEqual compares two JSON-able values by canonical serialization, so
// Go-typed slices ([]string vs []interface{}) compare equal.
func jsonEqual(a, b interface{}) bool {
	ra, err1 := json.Marshal(a)
	rb, err2 := json.Marshal(b)
	if err1 != nil || err2 != nil {
		return false
	}
	return string(ra) == string(rb)
}

func TestConformanceVerdicts(t *testing.T) {
	fixtures, err := LoadVerdicts()
	if err != nil {
		t.Fatal(err)
	}
	if len(fixtures) == 0 {
		t.Fatal("no verdict fixtures loaded")
	}
	var checked int
	for _, fixture := range fixtures {
		if !contains(fixture.Validators, "go") {
			continue
		}
		checked++
		verdict := Validate(FixtureEventToNostr(fixture.Event))
		if verdict.Accept != fixture.Expect.Accept {
			t.Errorf("%s: accept=%v expected=%v", fixture.ID, verdict.Accept, fixture.Expect.Accept)
			continue
		}
		if !fixture.Expect.Accept && verdict.Code != fixture.Expect.Code {
			t.Errorf("%s: code=%q expected=%q", fixture.ID, verdict.Code, fixture.Expect.Code)
		}
	}
	if checked == 0 {
		t.Fatal("no 'go' verdict fixtures run")
	}
}

func TestConformanceFolds(t *testing.T) {
	fixtures, err := LoadFolds()
	if err != nil {
		t.Fatal(err)
	}
	var checked int
	for _, fixture := range fixtures {
		if !contains(fixture.Validators, "go") {
			continue
		}
		events := make([]*nostr.Event, 0, len(fixture.Events))
		for _, e := range fixture.Events {
			events = append(events, FixtureEventToNostr(e))
		}
		result := Fold(fixture.Kind, events)
		checked++
		if result.Subject != fixture.Expect.Subject {
			t.Errorf("%s: subject=%q expected=%q", fixture.ID, result.Subject, fixture.Expect.Subject)
		}
		if result.Revision != fixture.Expect.Revision {
			t.Errorf("%s: revision=%d expected=%d", fixture.ID, result.Revision, fixture.Expect.Revision)
		}
		if result.Enabled != fixture.Expect.Enabled {
			t.Errorf("%s: enabled=%v expected=%v", fixture.ID, result.Enabled, fixture.Expect.Enabled)
		}
		if result.Conflicts != fixture.Expect.Conflicts {
			t.Errorf("%s: conflicts=%d expected=%d", fixture.ID, result.Conflicts, fixture.Expect.Conflicts)
		}
		if !jsonEqual(result.Fact, fixture.Expect.Fact) {
			t.Errorf("%s: fact=%v expected=%v", fixture.ID, result.Fact, fixture.Expect.Fact)
		}
	}
	if checked == 0 {
		t.Fatal("no 'go' fold fixtures run")
	}
}

func TestReasonCodeVocabulary(t *testing.T) {
	fixtures, err := LoadVerdicts()
	if err != nil {
		t.Fatal(err)
	}
	seen := map[string]bool{}
	for _, fixture := range fixtures {
		if !fixture.Expect.Accept {
			seen[fixture.Expect.Code] = true
		}
	}
	want := map[string]bool{
		"10000:bad-p": true, "10002:bad-r": true,
		"27236:bad-expiry": true, "27236:bad-tags": true, "27236:missing-scope": true,
		"27237:missing-e": true, "30000:bad-p": true,
		"31100:missing-type": true, "31100:scopes-not-array": true,
		"31101:missing-schema": true,
		"31102:admin-not-bool": true, "31102:bad-signer-type": true,
		"31102:enabled-not-bool": true, "31102:missing-username": true,
		"content-not-json": true, "d-not-hex64": true, "missing-d": true,
		"revision-invalid": true, "schema-invalid": true, "subject-mismatch": true,
	}
	for code := range want {
		if !seen[code] {
			t.Errorf("expected corpus code %q not exercised by a 'go' fixture", code)
		}
	}
}

func TestKindConstants(t *testing.T) {
	cases := map[int]string{
		KindOperationRequest: "KindOperationRequest",
		KindSystemEvent:      "KindSystemEvent",
		KindCapability:       "KindCapability",
		KindDelegation:       "KindDelegation",
		KindPermissionSet:    "KindPermissionSet",
	}
	for kind, name := range cases {
		if kind == 0 {
			t.Errorf("%s is 0", name)
		}
	}
	if KindOperationRequest != 2200 || KindCapability != 31100 || KindDelegation != 27236 {
		t.Fatalf("kind constants drifted")
	}
}

func TestClass(t *testing.T) {
	if Class(KindDelegation) != ClassImmutable {
		t.Error("delegation should be immutable")
	}
	if Class(KindCapability) != ClassReplaceable {
		t.Error("capability should be replaceable")
	}
	if Class(KindAuthChallenge) != ClassEphemeral {
		t.Error("auth challenge should be ephemeral")
	}
	if Class(KindOperationRequest) != ClassImmutable {
		t.Error("operation request should be immutable")
	}
}

func TestIsCustomKind(t *testing.T) {
	if !IsCustomKind(KindOperationRequest) {
		t.Error("operation request is custom")
	}
	if !IsCustomKind(KindIdentityDefinition) {
		t.Error("identity definition is custom")
	}
	if IsCustomKind(1) {
		t.Error("kind 1 should not be custom")
	}
}

func contains(list []string, target string) bool {
	for _, item := range list {
		if item == target {
			return true
		}
	}
	return false
}
