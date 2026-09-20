"""NostrHost control-plane event kind registry (Python binding).

Canonical kind constants for the NostrHost control-plane event protocol. The
machine-readable authority is ``spec/manifest.json``; these constants must stay
in sync with it (see the manifest tests).
"""

from __future__ import annotations

from enum import IntEnum


class Kind(IntEnum):
    # Replaceable lists (NIP-51 / NIP-65 / NIP-78).
    MuteList = 10000
    RelayList = 10002
    BlockedRelays = 10006
    PermissionSet = 30000
    AppData = 30078

    # Operation chain (immutable audit events).
    OperationRequest = 2200
    OperationApproval = 2201
    OperationRejection = 2202
    ExecutionStarted = 2203
    ExecutionResult = 2204
    ExecutionProgress = 2205

    # Notices (machine-state events).
    SystemEvent = 2210
    ServiceEvent = 2211
    BackupEvent = 2212
    SecurityEvent = 2213
    StateBundle = 2214

    # Standard / other.
    AuthChallenge = 22242
    OwnerApproval = 24243
    Nip98 = 27235

    # Delegations.
    Delegation = 27236
    DelegationRevocation = 27237

    # Addressable documents.
    RepositoryAnnouncement = 30617
    Capability = 31100
    TrustPolicy = 31101
    IdentityDefinition = 31102
    BuildAttestation = 31300


# Module-level int aliases so `from nostrhost_protocol import KindOperationRequest`
# works exactly like the Go constant names (and the old application constants).
AppData: int = Kind.AppData
AuthChallenge: int = Kind.AuthChallenge
BackupEvent: int = Kind.BackupEvent
BlockedRelays: int = Kind.BlockedRelays
BuildAttestation: int = Kind.BuildAttestation
Capability: int = Kind.Capability
Delegation: int = Kind.Delegation
DelegationRevocation: int = Kind.DelegationRevocation
ExecutionProgress: int = Kind.ExecutionProgress
ExecutionResult: int = Kind.ExecutionResult
ExecutionStarted: int = Kind.ExecutionStarted
IdentityDefinition: int = Kind.IdentityDefinition
MuteList: int = Kind.MuteList
Nip98: int = Kind.Nip98
OperationApproval: int = Kind.OperationApproval
OperationRejection: int = Kind.OperationRejection
OperationRequest: int = Kind.OperationRequest
OwnerApproval: int = Kind.OwnerApproval
PermissionSet: int = Kind.PermissionSet
RelayList: int = Kind.RelayList
RepositoryAnnouncement: int = Kind.RepositoryAnnouncement
SecurityEvent: int = Kind.SecurityEvent
ServiceEvent: int = Kind.ServiceEvent
StateBundle: int = Kind.StateBundle
SystemEvent: int = Kind.SystemEvent
TrustPolicy: int = Kind.TrustPolicy

# Go-style aliases (cross-language parity with the Go binding constant names).
KindAppData: int = Kind.AppData
KindAuthChallenge: int = Kind.AuthChallenge
KindBackupEvent: int = Kind.BackupEvent
KindBlockedRelays: int = Kind.BlockedRelays
KindBuildAttestation: int = Kind.BuildAttestation
KindCapability: int = Kind.Capability
KindDelegation: int = Kind.Delegation
KindDelegationRevocation: int = Kind.DelegationRevocation
KindExecutionProgress: int = Kind.ExecutionProgress
KindExecutionResult: int = Kind.ExecutionResult
KindExecutionStarted: int = Kind.ExecutionStarted
KindIdentityDefinition: int = Kind.IdentityDefinition
KindMuteList: int = Kind.MuteList
KindNip98: int = Kind.Nip98
KindOperationApproval: int = Kind.OperationApproval
KindOperationRejection: int = Kind.OperationRejection
KindOperationRequest: int = Kind.OperationRequest
KindOwnerApproval: int = Kind.OwnerApproval
KindPermissionSet: int = Kind.PermissionSet
KindRelayList: int = Kind.RelayList
KindRepositoryAnnouncement: int = Kind.RepositoryAnnouncement
KindSecurityEvent: int = Kind.SecurityEvent
KindServiceEvent: int = Kind.ServiceEvent
KindStateBundle: int = Kind.StateBundle
KindSystemEvent: int = Kind.SystemEvent
KindTrustPolicy: int = Kind.TrustPolicy

# One-release legacy aliases matching the historical application-level names.
KIND_MUTE_LIST: int = Kind.MuteList
KIND_RELAY_LIST: int = Kind.RelayList
KIND_BLOCKED_RELAYS: int = Kind.BlockedRelays
KIND_PERMISSION_SET: int = Kind.PermissionSet
KIND_APP_DATA: int = Kind.AppData
KIND_OPERATION_REQUEST: int = Kind.OperationRequest
KIND_OPERATION_APPROVAL: int = Kind.OperationApproval
KIND_OPERATION_REJECTION: int = Kind.OperationRejection
KIND_EXECUTION_STARTED: int = Kind.ExecutionStarted
KIND_EXECUTION_RESULT: int = Kind.ExecutionResult
KIND_EXECUTION_PROGRESS: int = Kind.ExecutionProgress
KIND_SYSTEM_EVENT: int = Kind.SystemEvent
KIND_SERVICE_EVENT: int = Kind.ServiceEvent
KIND_BACKUP_EVENT: int = Kind.BackupEvent
KIND_SECURITY_EVENT: int = Kind.SecurityEvent
KIND_STATE_BUNDLE: int = Kind.StateBundle
KIND_AUTH_CHALLENGE: int = Kind.AuthChallenge
KIND_OWNER_APPROVAL: int = Kind.OwnerApproval
KIND_NIP98: int = Kind.Nip98
KIND_DELEGATION: int = Kind.Delegation
KIND_DELEGATION_REVOCATION: int = Kind.DelegationRevocation
KIND_REPOSITORY_ANNOUNCEMENT: int = Kind.RepositoryAnnouncement
KIND_CAPABILITY: int = Kind.Capability
KIND_TRUST_POLICY: int = Kind.TrustPolicy
KIND_IDENTITY_DEFINITION: int = Kind.IdentityDefinition
KIND_BUILD_ATTESTATION: int = Kind.BuildAttestation

# Sets mirroring tools/event_protocol.py + the control-plane event model.
JSON_CONTENT_KINDS = frozenset({Kind.Capability, Kind.TrustPolicy, Kind.IdentityDefinition})
ADDRESSABLE_KINDS = frozenset(
    {
        Kind.Capability,
        Kind.TrustPolicy,
        Kind.IdentityDefinition,
        Kind.PermissionSet,
        Kind.AppData,
    }
)
HEX64_D_KINDS = frozenset({Kind.Capability, Kind.IdentityDefinition})
SIGNER_TYPES = frozenset({"nip07", "nip46", "passkey", "unknown"})

# Operation chain kinds in order (request -> approval -> ...).
CHAIN_KINDS = (
    Kind.OperationRequest,
    Kind.OperationApproval,
    Kind.OperationRejection,
    Kind.ExecutionStarted,
    Kind.ExecutionResult,
)

NOTICE_KINDS = frozenset(
    {Kind.SystemEvent, Kind.ServiceEvent, Kind.BackupEvent, Kind.SecurityEvent}
)

# Retention classes (mirrors the Go event model).
CLASS_IMMUTABLE = "immutable"
CLASS_REPLACEABLE = "replaceable"
CLASS_PRURABLE = "prunable"
CLASS_EPHEMERAL = "ephemeral"


def retention_class(kind: int) -> str:
    """Retention class for a kind (mirrors the Go relay's Class())."""
    if kind in (Kind.Delegation, Kind.DelegationRevocation):
        return CLASS_IMMUTABLE
    if 20000 <= kind <= 29999:
        return CLASS_EPHEMERAL
    if 10000 <= kind <= 19999 or 30000 <= kind <= 39999:
        return CLASS_REPLACEABLE
    return CLASS_IMMUTABLE


def is_custom_kind(kind: int) -> bool:
    """Whether *kind* belongs to the NostrHost control-plane event model."""
    return kind in {
        Kind.OperationRequest,
        Kind.OperationApproval,
        Kind.OperationRejection,
        Kind.ExecutionStarted,
        Kind.ExecutionResult,
        Kind.ExecutionProgress,
        Kind.SystemEvent,
        Kind.ServiceEvent,
        Kind.BackupEvent,
        Kind.SecurityEvent,
        Kind.StateBundle,
        Kind.Delegation,
        Kind.DelegationRevocation,
        Kind.Capability,
        Kind.TrustPolicy,
        Kind.IdentityDefinition,
        Kind.BuildAttestation,
    }


def chain_kinds() -> list[int]:
    """Operation chain kinds as a list of ints (Go-compatible)."""
    return [int(k) for k in CHAIN_KINDS]


def all_kinds() -> list[int]:
    """Every kind in the registry, sorted."""
    return sorted(int(m) for m in Kind)