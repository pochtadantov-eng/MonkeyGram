import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramPresentationData
import ItemListUI
import AccountContext
import MonkeyGramVisual
import PresentationDataUtils
import UndoUI

private final class MonkeyGramArguments {
    let toggleGifts: (Bool) -> Void
    let toggleBalance: (Bool) -> Void
    let updateStars: (String) -> Void
    let updateTon: (String) -> Void
    let save: () -> Void
    let openHistory: (MonkeyGramCurrency) -> Void
    let openInventory: () -> Void
    let clearInventory: () -> Void

    init(
        toggleGifts: @escaping (Bool) -> Void,
        toggleBalance: @escaping (Bool) -> Void,
        updateStars: @escaping (String) -> Void,
        updateTon: @escaping (String) -> Void,
        save: @escaping () -> Void,
        openHistory: @escaping (MonkeyGramCurrency) -> Void,
        openInventory: @escaping () -> Void,
        clearInventory: @escaping () -> Void
    ) {
        self.toggleGifts = toggleGifts
        self.toggleBalance = toggleBalance
        self.updateStars = updateStars
        self.updateTon = updateTon
        self.save = save
        self.openHistory = openHistory
        self.openInventory = openInventory
        self.clearInventory = clearInventory
    }
}

private enum MonkeyGramSection: Int32 {
    case access
    case gifts
    case balance
    case inventory
    case actions
    case info
}

private enum MonkeyGramEntry: ItemListNodeEntry {
    case accessStatus
    case giftsToggle(Bool)
    case giftsFooter
    case balanceToggle(Bool)
    case starsInput(String)
    case tonInput(String)
    case save
    case inventory
    case clearInventory
    case historyStars
    case historyTon
    case info

    var section: ItemListSectionId {
        switch self {
        case .accessStatus:
            return MonkeyGramSection.access.rawValue
        case .giftsToggle, .giftsFooter:
            return MonkeyGramSection.gifts.rawValue
        case .balanceToggle, .starsInput, .tonInput, .save:
            return MonkeyGramSection.balance.rawValue
        case .inventory, .clearInventory:
            return MonkeyGramSection.inventory.rawValue
        case .historyStars, .historyTon:
            return MonkeyGramSection.actions.rawValue
        case .info:
            return MonkeyGramSection.info.rawValue
        }
    }

    var stableId: Int32 {
        switch self {
        case .accessStatus: return 0
        case .giftsToggle: return 1
        case .giftsFooter: return 2
        case .balanceToggle: return 3
        case .starsInput: return 4
        case .tonInput: return 5
        case .save: return 6
        case .inventory: return 7
        case .clearInventory: return 8
        case .historyStars: return 9
        case .historyTon: return 10
        case .info: return 11
        }
    }

    static func == (lhs: MonkeyGramEntry, rhs: MonkeyGramEntry) -> Bool {
        switch (lhs, rhs) {
        case (.accessStatus, .accessStatus): return true
        case let (.giftsToggle(a), .giftsToggle(b)): return a == b
        case (.giftsFooter, .giftsFooter): return true
        case let (.balanceToggle(a), .balanceToggle(b)): return a == b
        case let (.starsInput(a), .starsInput(b)): return a == b
        case let (.tonInput(a), .tonInput(b)): return a == b
        case (.save, .save), (.inventory, .inventory), (.clearInventory, .clearInventory),
             (.historyStars, .historyStars), (.historyTon, .historyTon), (.info, .info):
            return true
        default:
            return false
        }
    }

    static func < (lhs: MonkeyGramEntry, rhs: MonkeyGramEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! MonkeyGramArguments
        let store = MonkeyGramVisualStore.shared
        switch self {
        case .accessStatus:
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain("Доступ: всегда открыт · без ключей активации (VisualGram LocalAppearance без Secure Enclave)."),
                sectionId: self.section
            )
        case let .giftsToggle(value):
            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: "Включить визуалку",
                value: value,
                sectionId: self.section,
                style: .blocks,
                updated: { arguments.toggleGifts($0) }
            )
        case .giftsFooter:
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain("Профиль «Отправить подарок», маркетплейс NFT (Cookie Heart и др.) — локальная покупка без Telegram payments."),
                sectionId: self.section
            )
        case let .balanceToggle(value):
            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: "Включить баланс",
                value: value,
                sectionId: self.section,
                style: .blocks,
                updated: { arguments.toggleBalance($0) }
            )
        case let .starsInput(value):
            return ItemListSingleLineInputItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: NSAttributedString(string: "Stars", font: Font.regular(17.0), textColor: presentationData.theme.list.itemPrimaryTextColor),
                text: value,
                placeholder: "0",
                type: .number,
                sectionId: self.section,
                textUpdated: { arguments.updateStars($0) },
                action: {}
            )
        case let .tonInput(value):
            return ItemListSingleLineInputItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: NSAttributedString(string: "TON / Grams", font: Font.regular(17.0), textColor: presentationData.theme.list.itemPrimaryTextColor),
                text: value,
                placeholder: "0",
                type: .decimal,
                sectionId: self.section,
                textUpdated: { arguments.updateTon($0) },
                action: {}
            )
        case .save:
            return ItemListActionItem(
                presentationData: presentationData,
                title: "Сохранить балансы",
                kind: .generic,
                alignment: .natural,
                sectionId: self.section,
                style: .blocks,
                action: { arguments.save() }
            )
        case .inventory:
            let count = store.ownedGifts.count
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: "Визуальные NFT / подарки",
                label: count == 0 ? "" : "\(count)",
                sectionId: self.section,
                style: .blocks,
                action: { arguments.openInventory() }
            )
        case .clearInventory:
            return ItemListActionItem(
                presentationData: presentationData,
                title: "Очистить инвентарь",
                kind: .destructive,
                alignment: .natural,
                sectionId: self.section,
                style: .blocks,
                action: { arguments.clearInventory() }
            )
        case .historyStars:
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: "История Stars",
                label: "",
                sectionId: self.section,
                style: .blocks,
                action: { arguments.openHistory(.stars) }
            )
        case .historyTon:
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: "История TON",
                label: "",
                sectionId: self.section,
                style: .blocks,
                action: { arguments.openHistory(.ton) }
            )
        case .info:
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain("MonkeyGram · без ключей. Stars/GRAM открывают обычные экраны Telegram; при включённой визуалке в истории видны локальные пополнения и списания (выключил — скрываются, но сохраняются). Подарки: «ещё → Отправить подарок»."),
                sectionId: self.section
            )
        }
    }
}

private struct MonkeyGramState: Equatable {
    var giftsEnabled: Bool
    var balanceEnabled: Bool
    var starsText: String
    var tonText: String
    var inventoryCount: Int
}

public func monkeyGramVisualSettingsController(context: AccountContext) -> ViewController {
    let store = MonkeyGramVisualStore.shared
    let initial = MonkeyGramState(
        giftsEnabled: store.visualGiftsEnabled,
        balanceEnabled: store.visualBalanceEnabled,
        starsText: store.starsBalance == 0 ? "" : String(format: "%g", store.starsBalance),
        tonText: store.tonBalance == 0 ? "" : String(format: "%g", store.tonBalance),
        inventoryCount: store.ownedGifts.count
    )

    let statePromise = ValuePromise(initial, ignoreRepeated: true)
    let stateValue = Atomic(value: initial)
    let updateState: ((MonkeyGramState) -> MonkeyGramState) -> Void = { f in
        statePromise.set(stateValue.modify { f($0) })
    }

    var presentControllerImpl: ((ViewController, Any?) -> Void)?
    var pushControllerImpl: ((ViewController) -> Void)?

    let arguments = MonkeyGramArguments(
        toggleGifts: { value in
            store.visualGiftsEnabled = value
            updateState { current in
                var current = current
                current.giftsEnabled = value
                return current
            }
        },
        toggleBalance: { value in
            store.visualBalanceEnabled = value
            updateState { current in
                var current = current
                current.balanceEnabled = value
                return current
            }
        },
        updateStars: { text in
            updateState { current in
                var current = current
                current.starsText = text
                return current
            }
        },
        updateTon: { text in
            updateState { current in
                var current = current
                current.tonText = text
                return current
            }
        },
        save: {
            let state = stateValue.with { $0 }
            let stars = Double(state.starsText.replacingOccurrences(of: ",", with: ".")) ?? 0
            let ton = Double(state.tonText.replacingOccurrences(of: ",", with: ".")) ?? 0
            store.saveBalances(stars: stars, ton: ton)
            let presentationData = context.sharedContext.currentPresentationData.with { $0 }
            presentControllerImpl?(UndoOverlayController(
                presentationData: presentationData,
                content: .succeed(text: "Балансы сохранены", timeout: 2.0, customUndoText: nil),
                elevatedLayout: false,
                action: { _ in false }
            ), nil)
        },
        openHistory: { currency in
            pushControllerImpl?(monkeyGramHistoryController(context: context, currency: currency))
        },
        openInventory: {
            pushControllerImpl?(monkeyGramInventoryController(context: context))
        },
        clearInventory: {
            store.clearInventory()
            updateState { current in
                var current = current
                current.inventoryCount = 0
                return current
            }
            let presentationData = context.sharedContext.currentPresentationData.with { $0 }
            presentControllerImpl?(UndoOverlayController(
                presentationData: presentationData,
                content: .succeed(text: "Инвентарь очищен", timeout: 2.0, customUndoText: nil),
                elevatedLayout: false,
                action: { _ in false }
            ), nil)
        }
    )

    let signal = combineLatest(
        queue: .mainQueue(),
        context.sharedContext.presentationData,
        statePromise.get()
    )
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        var entries: [MonkeyGramEntry] = [
            .accessStatus,
            .giftsToggle(state.giftsEnabled),
            .giftsFooter,
            .balanceToggle(state.balanceEnabled)
        ]
        if state.balanceEnabled {
            entries.append(contentsOf: [
                .starsInput(state.starsText),
                .tonInput(state.tonText),
                .save
            ])
        }
        entries.append(contentsOf: [
            .inventory,
            .clearInventory,
            .historyStars,
            .historyTon,
            .info
        ])

        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text("MonkeyGram"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: entries,
            style: .blocks,
            animateChanges: false
        )
        return (controllerState, (listState, arguments))
    }

    let controller = ItemListController(context: context, state: signal)
    presentControllerImpl = { [weak controller] c, a in
        controller?.present(c, in: .window(.root), with: a)
    }
    pushControllerImpl = { [weak controller] c in
        (controller?.navigationController as? NavigationController)?.pushViewController(c)
    }
    return controller
}

private enum HistoryListEntry: ItemListNodeEntry {
    case row(MonkeyGramHistoryEntry)
    case empty

    var section: ItemListSectionId { 0 }

    var stableId: Int32 {
        switch self {
        case .empty: return 0
        case let .row(entry):
            return Int32(entry.id.hashValue & 0x7fffffff)
        }
    }

    static func == (lhs: HistoryListEntry, rhs: HistoryListEntry) -> Bool {
        switch (lhs, rhs) {
        case (.empty, .empty): return true
        case let (.row(a), .row(b)): return a == b
        default: return false
        }
    }

    static func < (lhs: HistoryListEntry, rhs: HistoryListEntry) -> Bool {
        switch (lhs, rhs) {
        case (.empty, _): return true
        case (_, .empty): return false
        case let (.row(a), .row(b)):
            return a.at > b.at
        }
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        switch self {
        case .empty:
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain("Пока нет операций. Пополните баланс или купите подарок/NFT."),
                sectionId: self.section
            )
        case let .row(entry):
            let sign = entry.direction == "in" ? "+" : "−"
            let amount = String(format: "%@%g", sign, entry.amount)
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: entry.title,
                label: amount,
                sectionId: self.section,
                style: .blocks,
                action: {}
            )
        }
    }
}

func monkeyGramHistoryController(context: AccountContext, currency: MonkeyGramCurrency) -> ViewController {
    let title = currency == .stars ? "История Stars" : "История TON"
    let signal = context.sharedContext.presentationData
    |> map { presentationData -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let rows = MonkeyGramVisualStore.shared.history(for: currency)
        let entries: [HistoryListEntry] = rows.isEmpty ? [.empty] : rows.map { .row($0) }
        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text(title),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: entries,
            style: .blocks,
            emptyStateItem: nil,
            animateChanges: false
        )
        return (controllerState, (listState, () as Any))
    }

    return ItemListController(context: context, state: signal)
}

private enum InventoryListEntry: ItemListNodeEntry {
    case row(MonkeyGramOwnedGift)
    case empty

    var section: ItemListSectionId { 0 }

    var stableId: Int32 {
        switch self {
        case .empty: return 0
        case let .row(gift):
            return Int32(gift.id.hashValue & 0x7fffffff)
        }
    }

    static func == (lhs: InventoryListEntry, rhs: InventoryListEntry) -> Bool {
        switch (lhs, rhs) {
        case (.empty, .empty): return true
        case let (.row(a), .row(b)): return a == b
        default: return false
        }
    }

    static func < (lhs: InventoryListEntry, rhs: InventoryListEntry) -> Bool {
        switch (lhs, rhs) {
        case (.empty, _): return true
        case (_, .empty): return false
        case let (.row(a), .row(b)):
            return a.at > b.at
        }
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        switch self {
        case .empty:
            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain("Инвентарь пуст. Купите NFT на маркетплейсе с включённой визуалкой."),
                sectionId: self.section
            )
        case let .row(gift):
            let priceLabel: String
            switch gift.currency {
            case .stars:
                priceLabel = String(format: "%g ★", gift.price)
            case .ton:
                priceLabel = String(format: "%g TON", gift.price)
            }
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: gift.displayName,
                label: priceLabel,
                sectionId: self.section,
                style: .blocks,
                action: {}
            )
        }
    }
}

func monkeyGramInventoryController(context: AccountContext) -> ViewController {
    let signal = context.sharedContext.presentationData
    |> map { presentationData -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let rows = MonkeyGramVisualStore.shared.ownedGifts
        let entries: [InventoryListEntry] = rows.isEmpty ? [.empty] : rows.map { .row($0) }
        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text("Визуальные NFT"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: entries,
            style: .blocks,
            emptyStateItem: nil,
            animateChanges: false
        )
        return (controllerState, (listState, () as Any))
    }

    return ItemListController(context: context, state: signal)
}
