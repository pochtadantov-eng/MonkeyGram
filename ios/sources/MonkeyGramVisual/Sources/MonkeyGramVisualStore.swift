import Foundation

public enum MonkeyGramCurrency: String, Codable {
    case stars
    case ton
}

public struct MonkeyGramHistoryEntry: Codable, Equatable {
    public let id: String
    public let currency: MonkeyGramCurrency
    public let direction: String // "in" | "out"
    public let amount: Double
    public let title: String
    public let subtitle: String?
    public let at: TimeInterval

    public init(
        id: String,
        currency: MonkeyGramCurrency,
        direction: String,
        amount: Double,
        title: String,
        subtitle: String? = nil,
        at: TimeInterval = Date().timeIntervalSince1970
    ) {
        self.id = id
        self.currency = currency
        self.direction = direction
        self.amount = amount
        self.title = title
        self.subtitle = subtitle
        self.at = at
    }
}

/// Local-only visual balances / gifts for MonkeyGram. Does not touch Telegram servers.
public final class MonkeyGramVisualStore {
    public static let shared = MonkeyGramVisualStore()

    private let defaults = UserDefaults.standard
    private let prefix = "monkeygram.visual."

    private enum Key {
        static let gifts = "giftsEnabled"
        static let balance = "balanceEnabled"
        static let stars = "starsBalance"
        static let ton = "tonBalance"
        static let history = "history"
    }

    private init() {}

    public var visualGiftsEnabled: Bool {
        get { defaults.bool(forKey: prefix + Key.gifts) }
        set {
            defaults.set(newValue, forKey: prefix + Key.gifts)
            notify()
        }
    }

    public var visualBalanceEnabled: Bool {
        get { defaults.bool(forKey: prefix + Key.balance) }
        set {
            defaults.set(newValue, forKey: prefix + Key.balance)
            notify()
        }
    }

    public var starsBalance: Double {
        get { defaults.double(forKey: prefix + Key.stars) }
        set {
            defaults.set(newValue, forKey: prefix + Key.stars)
            notify()
        }
    }

    public var tonBalance: Double {
        get { defaults.double(forKey: prefix + Key.ton) }
        set {
            defaults.set(newValue, forKey: prefix + Key.ton)
            notify()
        }
    }

    public var history: [MonkeyGramHistoryEntry] {
        get {
            guard let data = defaults.data(forKey: prefix + Key.history) else { return [] }
            return (try? JSONDecoder().decode([MonkeyGramHistoryEntry].self, from: data)) ?? []
        }
        set {
            if let data = try? JSONEncoder().encode(Array(newValue.prefix(200))) {
                defaults.set(data, forKey: prefix + Key.history)
            }
            notify()
        }
    }

    public static let didChangeNotification = Notification.Name("MonkeyGramVisualStoreDidChange")

    private func notify() {
        NotificationCenter.default.post(name: Self.didChangeNotification, object: self)
    }

    public func saveBalances(stars: Double, ton: Double) {
        let nextStars = max(0, stars)
        let nextTon = max(0, ton)
        var entries: [MonkeyGramHistoryEntry] = []
        let now = Date().timeIntervalSince1970

        if nextStars > starsBalance {
            entries.append(MonkeyGramHistoryEntry(
                id: "in-stars-\(now)",
                currency: .stars,
                direction: "in",
                amount: nextStars - starsBalance,
                title: "Пополнение Stars",
                subtitle: "Визуальный баланс",
                at: now
            ))
        } else if nextStars < starsBalance {
            entries.append(MonkeyGramHistoryEntry(
                id: "adj-stars-\(now)",
                currency: .stars,
                direction: "out",
                amount: starsBalance - nextStars,
                title: "Корректировка Stars",
                subtitle: "Визуальный баланс",
                at: now
            ))
        }

        if nextTon > tonBalance {
            entries.append(MonkeyGramHistoryEntry(
                id: "in-ton-\(now)",
                currency: .ton,
                direction: "in",
                amount: nextTon - tonBalance,
                title: "Пополнение TON",
                subtitle: "Визуальный баланс",
                at: now + 0.001
            ))
        } else if nextTon < tonBalance {
            entries.append(MonkeyGramHistoryEntry(
                id: "adj-ton-\(now)",
                currency: .ton,
                direction: "out",
                amount: tonBalance - nextTon,
                title: "Корректировка TON",
                subtitle: "Визуальный баланс",
                at: now + 0.001
            ))
        }

        starsBalance = nextStars
        tonBalance = nextTon
        if !entries.isEmpty {
            history = entries + history
        }
    }

    @discardableResult
    public func spend(currency: MonkeyGramCurrency, amount: Double, title: String, subtitle: String? = nil) -> Bool {
        guard visualBalanceEnabled, amount > 0 else { return false }
        switch currency {
        case .stars:
            guard starsBalance >= amount else { return false }
            starsBalance = (starsBalance * 100 - amount * 100).rounded() / 100
        case .ton:
            guard tonBalance >= amount else { return false }
            tonBalance = (tonBalance * 10000 - amount * 10000).rounded() / 10000
        }
        let entry = MonkeyGramHistoryEntry(
            id: "out-\(currency.rawValue)-\(Date().timeIntervalSince1970)",
            currency: currency,
            direction: "out",
            amount: amount,
            title: title,
            subtitle: subtitle
        )
        history = [entry] + history
        return true
    }

    public func history(for currency: MonkeyGramCurrency) -> [MonkeyGramHistoryEntry] {
        history.filter { $0.currency == currency }
    }

    public var effectiveStarsBalanceInt64: Int64 {
        if visualBalanceEnabled {
            return Int64(starsBalance.rounded(.down))
        }
        return 0
    }

    public func displayStarsAmount(realValue: Int64) -> Int64 {
        if visualBalanceEnabled {
            return Int64(starsBalance.rounded(.down))
        }
        return realValue
    }

    public func displayTonAmount(realValue: Int64) -> Int64 {
        if visualBalanceEnabled {
            // Telegram TON amounts are often in nanotons; for visual UI we store whole TON
            // and convert to the same scale used by formatTonAmountText (nanotons = * 1e9).
            return Int64((tonBalance * 1_000_000_000).rounded())
        }
        return realValue
    }
}
