package protocol

import (
	"embed"
	"encoding/json"

	"github.com/nbd-wtf/go-nostr"
)

//go:embed testdata
var testDataFS embed.FS

// FixtureEvent is the corpus representation of a signed event.
type FixtureEvent struct {
	ID        string     `json:"id"`
	Kind      int        `json:"kind"`
	CreatedAt int64      `json:"created_at"`
	Tags      [][]string `json:"tags"`
	Content   string     `json:"content"`
	PubKey    string     `json:"pubkey"`
}

// VerdictFixture is one entry in verdicts.json.
type VerdictFixture struct {
	ID         string        `json:"id"`
	Validators []string      `json:"validators"`
	Event      FixtureEvent  `json:"event"`
	Expect     VerdictExpect `json:"expect"`
}

// VerdictExpect is the expected outcome of a verdict fixture.
type VerdictExpect struct {
	Accept bool   `json:"accept"`
	Code   string `json:"code"`
}

// FoldFixture is one entry in folds.json.
type FoldFixture struct {
	ID         string         `json:"id"`
	Validators []string       `json:"validators"`
	Kind       int            `json:"kind"`
	Events     []FixtureEvent `json:"events"`
	Expect     FoldExpect     `json:"expect"`
}

// FoldExpect is the expected outcome of a fold fixture.
type FoldExpect struct {
	Subject   string                 `json:"subject"`
	Revision  int                    `json:"revision"`
	Enabled   bool                   `json:"enabled"`
	Conflicts int                    `json:"conflicts"`
	Fact      map[string]interface{} `json:"fact"`
}

// LoadVerdicts reads verdicts.json from the embedded corpus.
func LoadVerdicts() ([]VerdictFixture, error) {
	raw, err := testDataFS.ReadFile("testdata/verdicts.json")
	if err != nil {
		return nil, err
	}
	var doc struct {
		Fixtures []VerdictFixture `json:"fixtures"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, err
	}
	return doc.Fixtures, nil
}

// LoadFolds reads folds.json from the embedded corpus.
func LoadFolds() ([]FoldFixture, error) {
	raw, err := testDataFS.ReadFile("testdata/folds.json")
	if err != nil {
		return nil, err
	}
	var doc struct {
		Fixtures []FoldFixture `json:"fixtures"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, err
	}
	return doc.Fixtures, nil
}

// FixtureEventToNostr converts a corpus event to a go-nostr event.
func FixtureEventToNostr(e FixtureEvent) *nostr.Event {
	tags := nostr.Tags{}
	for _, tag := range e.Tags {
		tags = append(tags, nostr.Tag(tag))
	}
	return &nostr.Event{
		ID:        e.ID,
		PubKey:    e.PubKey,
		CreatedAt: nostr.Timestamp(e.CreatedAt),
		Kind:      e.Kind,
		Tags:      tags,
		Content:   e.Content,
	}
}
