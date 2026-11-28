import Foundation
import TelegramCore

/// In-memory outgoing visual gift bubbles for chat history (no Telegram send).
/// Uses Engine* wrappers only (no direct Postbox import).
public enum MonkeyGramChatGiftBridge {
    private static let lock = NSLock()
    private static var byPeer: [EnginePeer.Id: [EngineRawMessage]] = [:]
    private static var nextLocalId: Int32 = -900_000

    public static func addOutgoingStarGift(
        accountPeerId: EnginePeer.Id,
        peerId: EnginePeer.Id,
        peer: EnginePeer?,
        accountPeer: EnginePeer?,
        gift: StarGift.Gift,
        text: String,
        entities: [MessageTextEntity],
        hideName: Bool,
        includeUpgrade: Bool
    ) {
        lock.lock()
        defer { lock.unlock() }

        nextLocalId -= 1
        let localId = nextLocalId
        let timestamp = Int32(Date().timeIntervalSince1970)

        var peers = EngineSimpleDictionary<EnginePeer.Id, EngineRawPeer>()
        if let peer {
            peers[peer.id] = peer._asPeer()
        }
        if let accountPeer {
            peers[accountPeer.id] = accountPeer._asPeer()
        }

        let media: [EngineRawMedia] = [
            TelegramMediaAction(
                action: .starGift(
                    gift: .generic(gift),
                    convertStars: gift.convertStars,
                    text: text.isEmpty ? nil : text,
                    entities: entities.isEmpty ? nil : entities,
                    nameHidden: hideName,
                    savedToProfile: false,
                    converted: false,
                    upgraded: false,
                    canUpgrade: gift.upgradeStars != nil,
                    upgradeStars: includeUpgrade ? gift.upgradeStars : nil,
                    isRefunded: false,
                    isPrepaidUpgrade: false,
                    upgradeMessageId: nil,
                    peerId: nil,
                    senderId: accountPeerId,
                    savedId: nil,
                    prepaidUpgradeHash: nil,
                    giftMessageId: nil,
                    upgradeSeparate: false,
                    isAuctionAcquired: false,
                    toPeerId: nil,
                    number: nil
                )
            )
        ]

        let message = EngineRawMessage(
            stableId: UInt32(bitPattern: localId),
            stableVersion: 0,
            id: EngineMessage.Id(peerId: peerId, namespace: Namespaces.Message.Local, id: localId),
            globallyUniqueId: Int64(localId),
            groupingKey: nil,
            groupInfo: nil,
            threadId: nil,
            timestamp: timestamp,
            flags: [],
            tags: [],
            globalTags: [],
            localTags: [],
            customTags: [],
            forwardInfo: nil,
            author: accountPeer.map { $0._asPeer() },
            text: "",
            attributes: [],
            media: media,
            peers: peers,
            associatedMessages: EngineSimpleDictionary<EngineMessage.Id, EngineRawMessage>(),
            associatedMessageIds: [],
            associatedMedia: [:],
            associatedThreadInfo: nil,
            associatedStories: [:]
        )
        byPeer[peerId, default: []].append(message)
    }

    public static func addOutgoingUniqueGift(
        accountPeerId: EnginePeer.Id,
        peerId: EnginePeer.Id,
        peer: EnginePeer?,
        accountPeer: EnginePeer?,
        gift: StarGift.UniqueGift,
        text: String?,
        entities: [MessageTextEntity]?
    ) {
        lock.lock()
        defer { lock.unlock() }

        nextLocalId -= 1
        let localId = nextLocalId
        let timestamp = Int32(Date().timeIntervalSince1970)

        var peers = EngineSimpleDictionary<EnginePeer.Id, EngineRawPeer>()
        if let peer {
            peers[peer.id] = peer._asPeer()
        }
        if let accountPeer {
            peers[accountPeer.id] = accountPeer._asPeer()
        }

        let media: [EngineRawMedia] = [
            TelegramMediaAction(
                action: .starGiftUnique(
                    gift: .unique(gift),
                    isUpgrade: false,
                    isTransferred: true,
                    savedToProfile: false,
                    canExportDate: nil,
                    transferStars: nil,
                    isRefunded: false,
                    isPrepaidUpgrade: false,
                    peerId: peerId,
                    senderId: accountPeerId,
                    savedId: nil,
                    resaleAmount: nil,
                    canTransferDate: nil,
                    canResaleDate: nil,
                    dropOriginalDetailsStars: nil,
                    assigned: false,
                    fromOffer: false,
                    canCraftAt: nil,
                    isCrafted: false,
                    text: text,
                    entities: entities,
                    nameHidden: false
                )
            )
        ]

        let message = EngineRawMessage(
            stableId: UInt32(bitPattern: localId),
            stableVersion: 0,
            id: EngineMessage.Id(peerId: peerId, namespace: Namespaces.Message.Local, id: localId),
            globallyUniqueId: Int64(localId),
            groupingKey: nil,
            groupInfo: nil,
            threadId: nil,
            timestamp: timestamp,
            flags: [],
            tags: [],
            globalTags: [],
            localTags: [],
            customTags: [],
            forwardInfo: nil,
            author: accountPeer.map { $0._asPeer() },
            text: "",
            attributes: [],
            media: media,
            peers: peers,
            associatedMessages: EngineSimpleDictionary<EngineMessage.Id, EngineRawMessage>(),
            associatedMessageIds: [],
            associatedMedia: [:],
            associatedThreadInfo: nil,
            associatedStories: [:]
        )
        byPeer[peerId, default: []].append(message)
    }

    public static func messages(for peerId: EnginePeer.Id) -> [EngineRawMessage] {
        lock.lock()
        defer { lock.unlock() }
        return byPeer[peerId] ?? []
    }
}
