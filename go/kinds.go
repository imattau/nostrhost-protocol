// Package protocol is the Go binding of the NostrHost control-plane event
// protocol. It mirrors the language-neutral spec (spec/envelope.md) and the
// Python binding (nostrhost_protocol) exactly: the conformance corpus must
// reach identical verdicts and folds across both.
//
// It supersedes the former libs/nostrhost-control/internal/eventmodel and
// internal/eventprotocol packages.
package protocol

// Kind constants for the NostrHost control-plane event model.
//
// The numbers match the machine-readable manifest (spec/manifest.json) and the
// Go-style names match the historical eventmodel constant names, so existing
// consumers migrate with a rename from `eventmodel.` to `protocol.`.
const (
	// Replaceable lists (NIP-51 / NIP-65 / NIP-78).
	KindMuteList               = 10000
	KindRelayList              = 10002
	KindBlockedRelays          = 10006
	KindPermissionSet          = 30000
	KindAppData                = 30078
	KindRepositoryAnnouncement = 30617

	// Operation chain (immutable audit events).
	KindOperationRequest   = 2200
	KindOperationApproval  = 2201
	KindOperationRejection = 2202
	KindExecutionStarted   = 2203
	KindExecutionResult    = 2204
	KindExecutionProgress  = 2205

	// Notices (machine-state events).
	KindSystemEvent   = 2210
	KindServiceEvent  = 2211
	KindBackupEvent   = 2212
	KindSecurityEvent = 2213
	KindStateBundle   = 2214

	// Standard / other.
	KindAuthChallenge = 22242
	KindOwnerApproval = 24243
	KindNip98         = 27235

	// Delegations.
	KindDelegation           = 27236
	KindDelegationRevocation = 27237

	// Addressable documents.
	KindCapability         = 31100
	KindTrustPolicy        = 31101
	KindIdentityDefinition = 31102
	KindBuildAttestation   = 31300
)

// Notice severities for system/service/backup/security events (2210-2213).
const (
	SeverityInfo     = "info"
	SeverityWarning  = "warning"
	SeverityCritical = "critical"
)

// Retention classes.
const (
	ClassImmutable   = "immutable"
	ClassReplaceable = "replaceable"
	ClassPrunable    = "prunable"
	ClassEphemeral   = "ephemeral"
)

// JSONContentKinds are the kinds whose content is defined to be a JSON object.
var JSONContentKinds = map[int]bool{
	KindCapability: true, KindTrustPolicy: true, KindIdentityDefinition: true,
}

// AddressableKinds are the kinds keyed by a `d` tag.
var AddressableKinds = map[int]bool{
	KindCapability: true, KindTrustPolicy: true, KindIdentityDefinition: true,
	KindPermissionSet: true, KindAppData: true,
}

// Hex64DKinds require the `d` tag to be a 64-hex pubkey.
var Hex64DKinds = map[int]bool{KindCapability: true, KindIdentityDefinition: true}

// SignerTypes are the allowed identity `signer_type` values.
var SignerTypes = map[string]bool{
	"nip07": true, "nip46": true, "passkey": true, "unknown": true,
}

// Class returns the retention class for a kind.
func Class(kind int) string {
	switch {
	case kind == KindDelegation || kind == KindDelegationRevocation:
		// Regular signed audit events despite the 27236/27237 range.
		return ClassImmutable
	case kind >= 20000 && kind <= 29999:
		return ClassEphemeral
	case kind >= 10000 && kind <= 19999, kind >= 30000 && kind <= 39999:
		return ClassReplaceable
	default:
		return ClassImmutable
	}
}

// IsCustomKind reports whether kind belongs to the NostrHost control-plane
// event model (and therefore gets schema validation).
func IsCustomKind(kind int) bool {
	switch kind {
	case KindOperationRequest, KindOperationApproval, KindOperationRejection,
		KindExecutionStarted, KindExecutionResult, KindExecutionProgress,
		KindSystemEvent, KindServiceEvent, KindBackupEvent, KindSecurityEvent,
		KindStateBundle, KindDelegation, KindDelegationRevocation,
		KindCapability, KindTrustPolicy, KindIdentityDefinition, KindBuildAttestation:
		return true
	}
	return false
}

// ChainKinds returns the operation chain kinds (request → approval → …).
func ChainKinds() []int {
	return []int{KindOperationRequest, KindOperationApproval, KindOperationRejection,
		KindExecutionStarted, KindExecutionResult}
}
