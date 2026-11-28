#!/usr/bin/env python3
"""Apply MonkeyGram visual-mod patches onto a Telegram-iOS checkout."""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def replace_once(path: pathlib.Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if new.strip() in text or label in text:
            print(f"skip (already applied): {label}")
            return
        die(f"pattern not found for {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched: {label}")


def insert_after(path: pathlib.Path, marker: str, insertion: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if insertion.strip() in text:
        print(f"skip (already applied): {label}")
        return
    if marker not in text:
        die(f"marker not found for {label} in {path}")
    path.write_text(text.replace(marker, marker + insertion, 1), encoding="utf-8")
    print(f"patched: {label}")


def ensure_dep(build_path: pathlib.Path, dep: str, label: str) -> None:
    text = build_path.read_text(encoding="utf-8")
    if dep in text:
        print(f"skip (dep present): {label}")
        return
    # Insert after deps = [
    m = re.search(r"deps\s*=\s*\[", text)
    if not m:
        die(f"deps block not found in {build_path}")
    idx = m.end()
    text = text[:idx] + f'\n        "{dep}",' + text[idx:]
    build_path.write_text(text, encoding="utf-8")
    print(f"patched: {label}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telegram-root", required=True, type=pathlib.Path)
    parser.add_argument("--overlay-root", required=True, type=pathlib.Path)
    args = parser.parse_args()

    tg = args.telegram_root.resolve()
    overlay = args.overlay_root.resolve()
    if not (tg / "versions.json").exists():
        die(f"not a Telegram-iOS tree: {tg}")

    # 1) Copy MonkeyGramVisual module
    src_mod = overlay / "sources" / "MonkeyGramVisual"
    dst_mod = tg / "submodules" / "MonkeyGramVisual"
    if dst_mod.exists():
        shutil.rmtree(dst_mod)
    shutil.copytree(src_mod, dst_mod)
    print(f"copied module -> {dst_mod}")

    # 2) Copy settings controller into PeerInfoScreen
    peer_info_sources = tg / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources"
    shutil.copy2(
        overlay / "sources" / "MonkeyGramVisualSettingsController.swift",
        peer_info_sources / "MonkeyGramVisualSettingsController.swift",
    )
    print("copied MonkeyGramVisualSettingsController.swift")

    # 3) Add Bazel deps
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "PeerInfoScreen -> MonkeyGramVisual",
    )
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "Gifts" / "GiftSetupScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "GiftSetupScreen -> MonkeyGramVisual",
    )
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "Stars" / "StarsTransactionsScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "StarsTransactionsScreen -> MonkeyGramVisual",
    )

    # 4) Settings section enum
    peer_info = peer_info_sources / "PeerInfoScreen.swift"
    replace_once(
        peer_info,
        "    case wallet\n}",
        "    case wallet\n    case monkeygram\n}",
        "PeerInfoSettingsSection.monkeygram",
    )

    # 5) Settings list item + visual balances / gifts
    settings_items = peer_info_sources / "PeerInfoSettingsItems.swift"
    insert_after(
        settings_items,
        "import WalletContext\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in settings items",
    )

    balance_block_old = """    if let starsState = data.starsState {
        if !isPremiumDisabled || abs(starsState.balance.value) > 0 {
            let balanceText: NSAttributedString
            if abs(starsState.balance.value) > 0 {
                let formattedLabel = formatStarsAmountText(starsState.balance, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 102, label: .attributedText(balanceText), text: presentationData.strings.Settings_Stars, icon: PresentationResourcesSettings.stars, action: {
                interaction.openSettings(.stars)
            }))
        }
    }
    if let tonState = data.tonState {
        if abs(tonState.balance.value) > 0 {
            let balanceText: NSAttributedString
            if abs(tonState.balance.value) > 0 {
                let formattedLabel = formatTonAmountText(tonState.balance.value, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 103, label: .attributedText(balanceText), text: presentationData.strings.Settings_MyTon, icon: PresentationResourcesSettings.gramEarnings, action: {
                interaction.openSettings(.ton)
            }))
        }
    }"""

    balance_block_new = """    let monkeyStore = MonkeyGramVisualStore.shared
    let visualBalanceOn = monkeyStore.visualBalanceEnabled
    if let starsState = data.starsState {
        let starsValue = visualBalanceOn ? StarsAmount(value: Int64(monkeyStore.starsBalance.rounded(.down)), nanos: 0) : starsState.balance
        if !isPremiumDisabled || abs(starsValue.value) > 0 || visualBalanceOn {
            let balanceText: NSAttributedString
            if abs(starsValue.value) > 0 || visualBalanceOn {
                let formattedLabel = formatStarsAmountText(starsValue, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 102, label: .attributedText(balanceText), text: presentationData.strings.Settings_Stars, icon: PresentationResourcesSettings.stars, action: {
                interaction.openSettings(.stars)
            }))
        }
    }
    if let tonState = data.tonState {
        let tonValue = visualBalanceOn ? Int64((monkeyStore.tonBalance * 1_000_000_000.0).rounded()) : tonState.balance.value
        if abs(tonValue) > 0 || visualBalanceOn {
            let balanceText: NSAttributedString
            if abs(tonValue) > 0 || visualBalanceOn {
                let formattedLabel = formatTonAmountText(tonValue, dateTimeFormat: presentationData.dateTimeFormat)
                let smallLabelFont = Font.regular(floor(presentationData.listsFontSize.itemListBaseFontSize / 17.0 * 13.0))
                let labelFont = Font.regular(presentationData.listsFontSize.itemListBaseFontSize)
                let labelColor = presentationData.theme.list.itemSecondaryTextColor
                balanceText = tonAmountAttributedString(formattedLabel, integralFont: labelFont, fractionalFont: smallLabelFont, color: labelColor, decimalSeparator: presentationData.dateTimeFormat.decimalSeparator)
            } else {
                balanceText = NSAttributedString()
            }
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 103, label: .attributedText(balanceText), text: presentationData.strings.Settings_MyTon, icon: PresentationResourcesSettings.gramEarnings, action: {
                interaction.openSettings(.ton)
            }))
        }
    }"""
    replace_once(settings_items, balance_block_old, balance_block_new, "visual Stars/TON balances")

    gift_old = """    if let starsState = data.starsState {
        if !isPremiumDisabled || starsState.balance > StarsAmount.zero {
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 105, label: .text(""), text: presentationData.strings.Settings_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                interaction.openSettings(.premiumGift)
            }))
        }
    }"""
    gift_new = """    if let starsState = data.starsState {
        if !isPremiumDisabled || starsState.balance > StarsAmount.zero || MonkeyGramVisualStore.shared.visualGiftsEnabled {
            items[.payment]!.append(PeerInfoScreenDisclosureItem(id: 105, label: .text(""), text: presentationData.strings.Settings_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                interaction.openSettings(.premiumGift)
            }))
        }
    }"""
    replace_once(settings_items, gift_old, gift_new, "always show Send Gift when visual gifts on")

    insert_after(
        settings_items,
        """    items[.support]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_Support, icon: PresentationResourcesSettings.support, action: {
        interaction.openSettings(.support)
    }))
""",
        """    items[.extra]!.append(PeerInfoScreenDisclosureItem(id: 50, text: "MonkeyGram", icon: PresentationResourcesSettings.premium, action: {
        interaction.openSettings(.monkeygram)
    }))
""",
        "MonkeyGram settings row",
    )

    # 6) openSettings handler
    settings_actions = peer_info_sources / "PeerInfoScreenSettingsActions.swift"
    insert_after(
        settings_actions,
        "import UndoUI\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in settings actions",
    )
    replace_once(
        settings_actions,
        """        case .wallet:
            guard WalletConfiguration.with(appConfiguration: self.context.currentAppConfiguration.with { $0 }).isAvailable else {
                self.controller?.present(UndoOverlayController(presentationData: self.presentationData, content: .info(title: nil, text: self.presentationData.strings.Wallet_Unavailable, timeout: nil, customUndoText: nil), action: { _ in return false }), in: .window(.root))
                return
            }
            push(self.context.sharedContext.makeWalletScreen(context: self.context))
        }
    }
""",
        """        case .wallet:
            guard WalletConfiguration.with(appConfiguration: self.context.currentAppConfiguration.with { $0 }).isAvailable else {
                self.controller?.present(UndoOverlayController(presentationData: self.presentationData, content: .info(title: nil, text: self.presentationData.strings.Wallet_Unavailable, timeout: nil, customUndoText: nil), action: { _ in return false }), in: .window(.root))
                return
            }
            push(self.context.sharedContext.makeWalletScreen(context: self.context))
        case .monkeygram:
            push(monkeyGramVisualSettingsController(context: self.context))
        }
    }
""",
        "openSettings(.monkeygram)",
    )

    # When visual balance enabled, Stars/TON screens open MonkeyGram history instead of (or before) real history
    replace_once(
        settings_actions,
        """        case .stars:
            if let starsContext = self.controller?.starsContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: starsContext))
            }
        case .ton:
            if let tonContext = self.controller?.tonContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: tonContext))
            }
""",
        """        case .stars:
            if MonkeyGramVisualStore.shared.visualBalanceEnabled {
                push(monkeyGramHistoryController(context: self.context, currency: .stars))
            } else if let starsContext = self.controller?.starsContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: starsContext))
            }
        case .ton:
            if MonkeyGramVisualStore.shared.visualBalanceEnabled {
                push(monkeyGramHistoryController(context: self.context, currency: .ton))
            } else if let tonContext = self.controller?.tonContext {
                push(self.context.sharedContext.makeStarsTransactionsScreen(context: self.context, starsContext: tonContext))
            }
""",
        "visual Stars/TON history routing",
    )

    # 7) Profile gift row when visual gifts enabled
    profile_items = peer_info_sources / "PeerInfoProfileItems.swift"
    insert_after(
        profile_items,
        "import BoostLevelIconComponent\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in profile items",
    )
    replace_once(
        profile_items,
        """                }, contextAction: birthdayContextAction, requestLayout: { _ in
                }))
            }
            
            var hasAbout = false
""",
        """                }, contextAction: birthdayContextAction, requestLayout: { _ in
                }))
            }

            if MonkeyGramVisualStore.shared.visualGiftsEnabled, user.id != context.account.peerId, user.botInfo == nil, !user.flags.contains(.isSupport) {
                items[currentPeerInfoSection]!.append(PeerInfoScreenActionItem(id: "monkeygram.sendGift", text: presentationData.strings.Profile_SendGift, icon: PresentationResourcesSettings.premiumGift, action: {
                    interaction.openPremiumGift()
                }))
            }
            
            var hasAbout = false
""",
        "profile Send Gift row (visual)",
    )
    # 8) GiftSetupScreen — always visual spend + chat plaque (never Telegram payments)
    gift_setup_dir = tg / "submodules" / "TelegramUI" / "Components" / "Gifts" / "GiftSetupScreen" / "Sources"
    gift_setup = gift_setup_dir / "GiftSetupScreen.swift"
    bridge_src = overlay / "sources" / "MonkeyGramChatGiftBridge.swift"
    if bridge_src.exists():
        shutil.copy2(bridge_src, gift_setup_dir / "MonkeyGramChatGiftBridge.swift")
        print("copied MonkeyGramChatGiftBridge.swift")
    insert_after(
        gift_setup,
        "import TelegramCore\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in GiftSetupScreen",
    )
    replace_once(
        gift_setup,
        """            if starsState.balance < StarsAmount(value: finalPrice, nanos: 0) {
                let _ = (self.optionsPromise.get()
                |> filter { $0 != nil }
                |> take(1)
                |> deliverOnMainQueue).startStandalone(next: { [weak self, starsContext] options in
                    guard let self, let component = self.component, let controller = self.environment?.controller() else {
                        return
                    }
                    let purchaseController = component.context.sharedContext.makeStarsPurchaseScreen(
                        context: component.context,
                        starsContext: starsContext,
                        options: options ?? [],
                        purpose: .starGift(peerId: component.peerId, requiredStars: finalPrice),
                        targetPeerId: nil,
                        customTheme: nil,
                        completion: { [weak self, weak starsContext] stars in
                            guard let self, let starsContext else {
                                return
                            }
                            self.inProgress = true
                            self.state?.updated()
                            
                            starsContext.add(balance: StarsAmount(value: stars, nanos: 0))
                            let _ = (starsContext.onUpdate
                            |> deliverOnMainQueue).start(next: {
                                proceed()
                            })
                        }
                    )
                    controller.push(purchaseController)
                })
            } else {
                proceed()
            }
""",
        """            // MonkeyGram: always local visual send — never call Telegram payments (avoids server «временно недоступен»).
            if MonkeyGramVisualStore.shared.interceptsGiftPurchases, let component = self.component, let controller = self.environment?.controller() {
                let presentationData = component.context.sharedContext.currentPresentationData.with { $0 }
                let ok = MonkeyGramVisualStore.shared.spend(
                    currency: .stars,
                    amount: Double(finalPrice),
                    title: "Подарок",
                    subtitle: "Визуальная отправка"
                )
                if !ok {
                    let alertController = textAlertController(context: component.context, title: nil, text: "Недостаточно визуальных Stars. Пополните баланс в Настройки → MonkeyGram.", actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})])
                    controller.present(alertController, in: .window(.root))
                    return
                }
                if case let .starGift(starGift, _) = component.subject {
                    let peer = self.peerMap[component.peerId]?._asPeer()
                    MonkeyGramChatGiftBridge.addOutgoingStarGift(
                        accountPeerId: component.context.account.peerId,
                        peerId: component.peerId,
                        peer: peer,
                        accountPeer: nil,
                        gift: starGift,
                        text: textInputText.string,
                        entities: entities,
                        hideName: self.hideName,
                        includeUpgrade: self.includeUpgrade
                    )
                    monkeyGramRecordOwnedGift(starGift: starGift, price: Double(finalPrice))
                }
                let complete = component.completion
                if let navigationController = controller.navigationController as? NavigationController {
                    var controllers = navigationController.viewControllers
                    controllers = controllers.filter { !($0 is GiftSetupScreen) && !($0 is GiftOptionsScreenProtocol) && !($0 is PeerInfoScreen) && !($0 is ContactSelectionController) }
                    var foundController = false
                    for c in controllers.reversed() {
                        if let chatController = c as? ChatController, case .peer(id: component.peerId) = chatController.chatLocation {
                            chatController.hintPlayNextOutgoingGift()
                            foundController = true
                            break
                        }
                    }
                    if !foundController {
                        let chatController = component.context.sharedContext.makeChatController(context: component.context, chatLocation: .peer(id: component.peerId), subject: nil, botStart: nil, mode: .standard(.default), params: nil)
                        chatController.hintPlayNextOutgoingGift()
                        controllers.append(chatController)
                    }
                    navigationController.setViewControllers(controllers, animated: true)
                    navigationController.view.addSubview(ConfettiView(frame: navigationController.view.bounds))
                    let toast = UndoOverlayController(presentationData: presentationData, content: .succeed(text: "Визуальный подарок · −\\(finalPrice) Stars", timeout: 2.5, customUndoText: nil), elevatedLayout: false, action: { _ in false })
                    (navigationController.viewControllers.last as? ViewController)?.present(toast, in: .current)
                } else {
                    controller.dismiss()
                }
                complete?()
            } else if starsState.balance < StarsAmount(value: finalPrice, nanos: 0) {
                let _ = (self.optionsPromise.get()
                |> filter { $0 != nil }
                |> take(1)
                |> deliverOnMainQueue).startStandalone(next: { [weak self, starsContext] options in
                    guard let self, let component = self.component, let controller = self.environment?.controller() else {
                        return
                    }
                    let purchaseController = component.context.sharedContext.makeStarsPurchaseScreen(
                        context: component.context,
                        starsContext: starsContext,
                        options: options ?? [],
                        purpose: .starGift(peerId: component.peerId, requiredStars: finalPrice),
                        targetPeerId: nil,
                        customTheme: nil,
                        completion: { [weak self, weak starsContext] stars in
                            guard let self, let starsContext else {
                                return
                            }
                            self.inProgress = true
                            self.state?.updated()
                            
                            starsContext.add(balance: StarsAmount(value: stars, nanos: 0))
                            let _ = (starsContext.onUpdate
                            |> deliverOnMainQueue).start(next: {
                                proceed()
                            })
                        }
                    )
                    controller.push(purchaseController)
                })
            } else {
                proceed()
            }
""",
        "GiftSetupScreen visual spend",
    )
    # Helper to record ordinary gift into inventory (appended near bridge file usage)
    helper_path = gift_setup_dir / "MonkeyGramGiftHelpers.swift"
    if not helper_path.exists() or "monkeyGramRecordOwnedGift" not in helper_path.read_text(encoding="utf-8"):
        helper_path.write_text(
            """import Foundation
import TelegramCore
import MonkeyGramVisual

func monkeyGramRecordOwnedGift(starGift: StarGift.Gift, price: Double) {
    let gift = MonkeyGramOwnedGift(
        slug: "gift-\\(starGift.id)",
        title: "Gift",
        number: 0,
        currency: .stars,
        price: price
    )
    var owned = MonkeyGramVisualStore.shared.ownedGifts
    owned.insert(gift, at: 0)
    MonkeyGramVisualStore.shared.ownedGifts = owned
}
""",
            encoding="utf-8",
        )
        print("wrote MonkeyGramGiftHelpers.swift")

    # 9) GiftViewScreen marketplace visual buy (Cookie Heart / NFT resale)
    ensure_dep(
        tg / "submodules" / "TelegramUI" / "Components" / "Gifts" / "GiftViewScreen" / "BUILD",
        "//submodules/MonkeyGramVisual:MonkeyGramVisual",
        "GiftViewScreen -> MonkeyGramVisual",
    )
    gift_view = (
        tg
        / "submodules"
        / "TelegramUI"
        / "Components"
        / "Gifts"
        / "GiftViewScreen"
        / "Sources"
        / "GiftViewScreen.swift"
    )
    insert_after(
        gift_view,
        "import TelegramCore\n",
        "import MonkeyGramVisual\nimport GiftSetupScreen\n",
        "import MonkeyGramVisual in GiftViewScreen",
    )
    replace_once(
        gift_view,
        """        func commitBuy(acceptedPrice: CurrencyAmount? = nil, skipConfirmation: Bool = false) {
            guard case let .unique(uniqueGift) = self.subject.arguments?.gift, let controller = self.getController() as? GiftViewScreen else {
                return
            }
            
            let context = self.context
            let presentationData = self.context.sharedContext.currentPresentationData.with { $0 }
            let giftTitle = "\\(uniqueGift.title) #\\(formatCollectibleNumber(uniqueGift.number, dateTimeFormat: presentationData.dateTimeFormat))"
            
            if let resellTooEarlyTimestamp = self.resellTooEarlyTimestamp {
""",
        """        func commitBuy(acceptedPrice: CurrencyAmount? = nil, skipConfirmation: Bool = false) {
            guard case let .unique(uniqueGift) = self.subject.arguments?.gift, let controller = self.getController() as? GiftViewScreen else {
                return
            }
            
            let context = self.context
            let presentationData = self.context.sharedContext.currentPresentationData.with { $0 }
            let giftTitle = "\\(uniqueGift.title) #\\(formatCollectibleNumber(uniqueGift.number, dateTimeFormat: presentationData.dateTimeFormat))"
            
            let monkey = MonkeyGramVisualStore.shared
            if monkey.interceptsGiftPurchases {
                let resell = acceptedPrice
                    ?? uniqueGift.resellAmounts?.first(where: { $0.currency == .ton })
                    ?? uniqueGift.resellAmounts?.first
                guard let resell else {
                    let alertController = textAlertController(context: context, title: nil, text: presentationData.strings.Gift_Buy_ErrorUnknown, actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})], parseMarkdown: true)
                    controller.present(alertController, in: .window(.root))
                    return
                }
                let currency: MonkeyGramCurrency
                let price: Double
                switch resell.currency {
                case .ton:
                    currency = .ton
                    price = MonkeyGramVisualStore.tonFromNanotons(resell.amount.value)
                case .stars:
                    currency = .stars
                    price = Double(resell.amount.value)
                }
                let ok = monkey.buyMarketplaceGift(
                    slug: uniqueGift.slug,
                    title: uniqueGift.title,
                    number: uniqueGift.number,
                    currency: currency,
                    price: price
                )
                if ok {
                    let recipientPeerId = self.recipientPeerId ?? context.account.peerId
                    if recipientPeerId != context.account.peerId {
                        MonkeyGramChatGiftBridge.addOutgoingUniqueGift(
                            accountPeerId: context.account.peerId,
                            peerId: recipientPeerId,
                            peer: nil,
                            accountPeer: nil,
                            gift: uniqueGift,
                            text: nil,
                            entities: nil
                        )
                    }
                    let unit = currency == .ton ? "TON" : "Stars"
                    let text = "Визуальная покупка · \\(giftTitle) · −\\(String(format: \"%g\", price)) \\(unit)"
                    controller.present(UndoOverlayController(presentationData: presentationData, content: .succeed(text: text, timeout: 2.5, customUndoText: nil), elevatedLayout: false, action: { _ in false }), in: .window(.root))
                    if let navigationController = controller.navigationController as? NavigationController {
                        navigationController.view.addSubview(ConfettiView(frame: navigationController.view.bounds))
                        if recipientPeerId != context.account.peerId {
                            var controllers = navigationController.viewControllers
                            controllers = controllers.filter { !($0 is GiftViewScreen) }
                            var found = false
                            for c in controllers.reversed() {
                                if let chatController = c as? ChatController, case .peer(id: recipientPeerId) = chatController.chatLocation {
                                    chatController.hintPlayNextOutgoingGift()
                                    found = true
                                    break
                                }
                            }
                            if !found {
                                let chatController = context.sharedContext.makeChatController(context: context, chatLocation: .peer(id: recipientPeerId), subject: nil, botStart: nil, mode: .standard(.default), params: nil)
                                chatController.hintPlayNextOutgoingGift()
                                controllers.append(chatController)
                            }
                            navigationController.setViewControllers(controllers, animated: true)
                            return
                        }
                    }
                    controller.dismissAnimated()
                } else {
                    let alertController = textAlertController(context: context, title: nil, text: "Недостаточно визуального баланса. Настройки → MonkeyGram.", actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})], parseMarkdown: true)
                    controller.present(alertController, in: .window(.root))
                }
                return
            }
            
            if let resellTooEarlyTimestamp = self.resellTooEarlyTimestamp {
""",
        "GiftViewScreen.commitBuy visual marketplace",
    )

    # 10) GiftViewBuyGift — intercept real buyStarGift API when visual on
    gift_buy = (
        tg
        / "submodules"
        / "TelegramUI"
        / "Components"
        / "Gifts"
        / "GiftViewScreen"
        / "Sources"
        / "GiftViewBuyGift.swift"
    )
    insert_after(
        gift_buy,
        "import TelegramCore\n",
        "import MonkeyGramVisual\n",
        "import MonkeyGramVisual in GiftViewBuyGift",
    )
    insert_after(
        gift_buy,
        "import GiftSetupScreen\n",
        "import UndoUI\n",
        "import UndoUI in GiftViewBuyGift",
    )
    replace_once(
        gift_buy,
        """        let proceed: () -> Void = {
            updateProgress(true)
            
            let buyGiftImpl: ((String, EnginePeer.Id, CurrencyAmount?, Bool, String?, [MessageTextEntity]?) -> Signal<Never, BuyStarGiftError>)
            if let buyGift {
                buyGiftImpl = { slug, peerId, price, hideName, text, entities in
                    return buyGift(slug, peerId, price, hideName, text, entities)
                }
            } else {
                buyGiftImpl = { slug, peerId, price, hideName, text, entities in
                    return context.engine.payments.buyStarGift(slug: slug, peerId: peerId, price: price, hideName: hideName, text: text, entities: entities)
                }
            }
            
            let _ = (buyGiftImpl(uniqueGift.slug, recipientPeerId, finalPrice, message.hideName, message.text, message.entities)
""",
        """        let proceed: () -> Void = {
            updateProgress(true)
            
            let monkey = MonkeyGramVisualStore.shared
            if monkey.interceptsGiftPurchases {
                let currency: MonkeyGramCurrency
                let price: Double
                switch finalPrice.currency {
                case .ton:
                    currency = .ton
                    price = MonkeyGramVisualStore.tonFromNanotons(finalPrice.amount.value)
                case .stars:
                    currency = .stars
                    price = Double(finalPrice.amount.value)
                }
                let ok = monkey.buyMarketplaceGift(
                    slug: uniqueGift.slug,
                    title: uniqueGift.title,
                    number: uniqueGift.number,
                    currency: currency,
                    price: price
                )
                beforeCompletion()
                updateProgress(false)
                if ok {
                    if let controller = getController() {
                        let unit = currency == .ton ? "TON" : "Stars"
                        let giftTitle = "\\(uniqueGift.title) #\\(uniqueGift.number)"
                        let text = "Визуальная покупка · \\(giftTitle) · −\\(String(format: \"%g\", price)) \\(unit)"
                        controller.present(UndoOverlayController(presentationData: presentationData, content: .succeed(text: text, timeout: 2.5, customUndoText: nil), elevatedLayout: false, action: { _ in false }), in: .window(.root))
                    }
                    completion()
                } else if let controller = getController() {
                    let alertController = textAlertController(context: context, title: nil, text: "Недостаточно визуального баланса. Настройки → MonkeyGram.", actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})], parseMarkdown: true)
                    controller.present(alertController, in: .window(.root))
                }
                return
            }
            
            let buyGiftImpl: ((String, EnginePeer.Id, CurrencyAmount?, Bool, String?, [MessageTextEntity]?) -> Signal<Never, BuyStarGiftError>)
            if let buyGift {
                buyGiftImpl = { slug, peerId, price, hideName, text, entities in
                    return buyGift(slug, peerId, price, hideName, text, entities)
                }
            } else {
                buyGiftImpl = { slug, peerId, price, hideName, text, entities in
                    return context.engine.payments.buyStarGift(slug: slug, peerId: peerId, price: price, hideName: hideName, text: text, entities: entities)
                }
            }
            
            let _ = (buyGiftImpl(uniqueGift.slug, recipientPeerId, finalPrice, message.hideName, message.text, message.entities)
""",
        "GiftViewBuyGift visual buyStarGift intercept",
    )

    # 11) Stars balance overlay — show visual Stars/TON on gift screens
    stars_balance = (
        tg
        / "submodules"
        / "TelegramUI"
        / "Components"
        / "Stars"
        / "StarsTransactionsScreen"
        / "Sources"
        / "StarsBalanceComponent.swift"
    )
    if stars_balance.exists():
        insert_after(
            stars_balance,
            "import TelegramCore\n",
            "import MonkeyGramVisual\n",
            "import MonkeyGramVisual in StarsBalanceComponent",
        )
        print(f"note: StarsBalanceComponent present at {stars_balance.name}")

    overlay_balance = (
        tg
        / "submodules"
        / "TelegramUI"
        / "Components"
        / "Stars"
        / "StarsBalanceOverlayComponent"
        / "Sources"
        / "StarsBalanceOverlayComponent.swift"
    )
    if overlay_balance.exists():
        ensure_dep(
            tg
            / "submodules"
            / "TelegramUI"
            / "Components"
            / "Stars"
            / "StarsBalanceOverlayComponent"
            / "BUILD",
            "//submodules/MonkeyGramVisual:MonkeyGramVisual",
            "StarsBalanceOverlayComponent -> MonkeyGramVisual",
        )
        insert_after(
            overlay_balance,
            "import TelegramCore\n",
            "import MonkeyGramVisual\n",
            "import MonkeyGramVisual in StarsBalanceOverlay",
        )
        replace_once(
            overlay_balance,
            """                            self.starsBalance = starsState?.balance.value ?? 0
                            self.tonBalance = tonState?.balance.value ?? 0
""",
            """                            let monkey = MonkeyGramVisualStore.shared
                            if monkey.visualBalanceEnabled {
                                self.starsBalance = Int64(monkey.starsBalance.rounded(.down))
                                self.tonBalance = Int64((monkey.tonBalance * 1_000_000_000.0).rounded())
                            } else {
                                self.starsBalance = starsState?.balance.value ?? 0
                                self.tonBalance = tonState?.balance.value ?? 0
                            }
""",
            "StarsBalanceOverlay visual balances",
        )

    # 12) Inject visual gift plaques into chat history
    chat_history = tg / "submodules" / "TelegramUI" / "Sources" / "ChatHistoryEntriesForView.swift"
    if chat_history.exists():
        insert_after(
            chat_history,
            "import TelegramCore\n",
            "import GiftSetupScreen\n",
            "import GiftSetupScreen in ChatHistoryEntriesForView",
        )
        replace_once(
            chat_history,
            """    if reverse {
        return (entries.reversed(), currentState)
    } else {
//        #if DEBUG
//        assert(entries.map(\\.stableId) == entries.sorted().map(\\.stableId))
//        #endif
        return (entries, currentState)
    }
}
""",
            """    if let peerId = location.peerId {
        for message in MonkeyGramChatGiftBridge.messages(for: peerId) {
            let already = entries.contains(where: { entry in
                if case let .MessageEntry(existing, _, _, _, _, _) = entry {
                    return existing.id == message.id
                }
                return false
            })
            if already {
                continue
            }
            entries.append(.MessageEntry(message, presentationData, false, nil, .none, ChatMessageEntryAttributes(rank: nil, isContact: false, contentTypeHint: .generic, updatingMedia: nil, isPlaying: false, isCentered: false, authorStoryStats: nil, displayContinueThreadFooter: false, pinToTop: false)))
        }
    }

    if reverse {
        return (entries.reversed(), currentState)
    } else {
//        #if DEBUG
//        assert(entries.map(\\.stableId) == entries.sorted().map(\\.stableId))
//        #endif
        return (entries, currentState)
    }
}
""",
            "ChatHistoryEntriesForView visual gift plaques",
        )

    # 13) GiftView marketplace: also drop plaque when gifting unique NFT to another peer
    # (commitBuy visual path already present; enrich success branch via secondary replace if needed)

    # 14) Rename app display name
    telegram_build = tg / "Telegram" / "BUILD"
    replace_once(
        telegram_build,
        """    <key>CFBundleDisplayName</key>
    <string>Telegram</string>
""",
        """    <key>CFBundleDisplayName</key>
    <string>MonkeyGram</string>
""",
        "CFBundleDisplayName MonkeyGram",
    )

    # 13) Optional configuration overlay
    conf_src = overlay / "configuration" / "monkeygram-configuration.json"
    conf_dst = tg / "build-system" / "monkeygram-configuration.json"
    if conf_src.exists():
        shutil.copy2(conf_src, conf_dst)
        print(f"copied {conf_dst.name}")

    print("MonkeyGram patches applied successfully.")


if __name__ == "__main__":
    main()
