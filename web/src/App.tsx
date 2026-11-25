import { useMemo, useState, type ReactNode } from 'react'
import {
  ME,
  chats as seedChats,
  contactById,
  contacts,
  gifts,
  messages as seedMessages,
  type Chat,
  type Contact,
  type GiftItem,
  type Message,
} from './data/mock'
import { useVisual } from './hooks/useVisual'
import {
  historyFor,
  saveBalances,
  setVisualBalanceEnabled,
  setVisualGiftsEnabled,
  spendVisual,
  type Currency,
} from './store/visualStore'

type Screen =
  | { name: 'chats' }
  | { name: 'chat'; chatId: string }
  | { name: 'profile'; contactId: string }
  | { name: 'settings' }
  | { name: 'monkeygram' }
  | { name: 'gifts'; contactId?: string }
  | { name: 'wallet' }
  | { name: 'history'; currency: Currency }

function initials(name: string) {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function formatAmount(n: number, currency: Currency) {
  if (currency === 'ton') return n.toLocaleString('ru-RU', { maximumFractionDigits: 4 })
  return n.toLocaleString('ru-RU', { maximumFractionDigits: 2 })
}

function BackIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M15 18l-6-6 6-6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
      <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function MenuIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M3.4 20.6l17.8-8.1c.9-.4.9-1.7 0-2.1L3.4 2.3c-.8-.4-1.7.3-1.5 1.2L4 10l9 2-9 2-2.1 6.5c-.2.9.7 1.6 1.5 1.1z" />
    </svg>
  )
}

export default function App() {
  const visual = useVisual()
  const [screen, setScreen] = useState<Screen>({ name: 'chats' })
  const [chatList, setChatList] = useState<Chat[]>(seedChats)
  const [msgs, setMsgs] = useState<Message[]>(seedMessages)
  const [draft, setDraft] = useState('')
  const [toast, setToast] = useState<string | null>(null)
  const [starsInput, setStarsInput] = useState(String(visual.starsBalance))
  const [tonInput, setTonInput] = useState(String(visual.tonBalance))
  const [giftTab, setGiftTab] = useState<'gift' | 'nft'>('gift')

  const showToast = (text: string) => {
    setToast(text)
    window.setTimeout(() => setToast(null), 2200)
  }

  const openMonkeygram = () => {
    setStarsInput(String(visual.starsBalance))
    setTonInput(String(visual.tonBalance))
    setScreen({ name: 'monkeygram' })
  }

  const sortedChats = useMemo(
    () => [...chatList].sort((a, b) => Number(!!b.pinned) - Number(!!a.pinned)),
    [chatList],
  )

  const touchChat = (chatId: string, lastMessage: string, time: string) => {
    setChatList((prev) =>
      prev.map((c) => (c.id === chatId ? { ...c, lastMessage, time, unread: 0 } : c)),
    )
  }

  const buyOrSend = (item: GiftItem, contact?: Contact) => {
    const currency: Currency = item.priceTon != null ? 'ton' : 'stars'
    const amount = item.priceTon ?? item.priceStars ?? 0
    if (!visual.visualBalanceEnabled) {
      showToast('Включите визуальный баланс в настройках MonkeyGram')
      return
    }
    if (!visual.visualGiftsEnabled && contact) {
      showToast('Включите визуальные подарки')
      return
    }

    const title = contact
      ? `Подарок · ${item.name}`
      : item.kind === 'nft'
        ? `Покупка NFT · ${item.name}`
        : `Покупка · ${item.name}`
    const subtitle = contact ? `@${contact.username}` : 'Визуальная витрина'

    const result = spendVisual(currency, amount, title, subtitle)
    if (!result.ok) {
      showToast(result.reason)
      return
    }

    if (contact) {
      const chat = chatList.find((c) => c.contactId === contact.id)
      if (chat) {
        const now = new Date()
        const time = `${now.getHours().toString().padStart(2, '0')}:${now
          .getMinutes()
          .toString()
          .padStart(2, '0')}`
        const text = `🎁 Отправлен подарок: ${item.emoji} ${item.name}`
        setMsgs((prev) => [
          ...prev,
          {
            id: `gift-${Date.now()}`,
            chatId: chat.id,
            fromMe: true,
            text,
            time,
          },
        ])
        touchChat(chat.id, text, time)
        setScreen({ name: 'chat', chatId: chat.id })
      } else {
        setScreen({ name: 'profile', contactId: contact.id })
      }
      showToast(`Подарок «${item.name}» отправлен визуально`)
    } else {
      showToast(`Куплено: ${item.name}`)
      setScreen({ name: 'history', currency })
    }
  }

  const saveVisualBalances = () => {
    const stars = Number(String(starsInput).replace(',', '.'))
    const ton = Number(String(tonInput).replace(',', '.'))
    if (!Number.isFinite(stars) || !Number.isFinite(ton)) {
      showToast('Введите корректные числа')
      return
    }
    saveBalances(stars, ton)
    showToast('Балансы сохранены')
  }

  let body: ReactNode = null

  if (screen.name === 'chats') {
    body = (
      <div className="screen" key="chats">
        <div className="topbar">
          <button className="icon-btn" aria-label="Меню" onClick={() => setScreen({ name: 'settings' })}>
            <MenuIcon />
          </button>
          <div className="brand-mark" style={{ flex: 1 }}>
            <div className="logo">🐵</div>
            <h1>MonkeyGram</h1>
          </div>
          <button className="icon-btn" aria-label="Кошелёк" onClick={() => setScreen({ name: 'wallet' })}>
            ★
          </button>
        </div>
        <div className="search-bar">
          <SearchIcon />
          Поиск
        </div>
        <div className="list">
          {sortedChats.map((chat) => {
            const c = contactById(chat.contactId)
            return (
              <button
                key={chat.id}
                className="chat-row"
                onClick={() => setScreen({ name: 'chat', chatId: chat.id })}
              >
                <div className="avatar" style={{ background: c.color }}>
                  {initials(c.name)}
                  {c.online && <span className="online-dot" />}
                </div>
                <div className="row-main">
                  <div className="row-title">
                    <span>{c.name}</span>
                    <span className="time">{chat.time}</span>
                  </div>
                  <div className="row-sub">
                    <span>{chat.lastMessage}</span>
                    {chat.unread > 0 && <span className="badge">{chat.unread}</span>}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  if (screen.name === 'chat') {
    const chat = chatList.find((c) => c.id === screen.chatId)!
    const contact = contactById(chat.contactId)
    const chatMsgs = msgs.filter((m) => m.chatId === chat.id)

    body = (
      <div className="screen" key={`chat-${chat.id}`}>
        <div className="topbar">
          <button className="icon-btn" onClick={() => setScreen({ name: 'chats' })} aria-label="Назад">
            <BackIcon />
          </button>
          <button
            className="chat-row"
            style={{ padding: 0, flex: 1, color: '#fff' }}
            onClick={() => setScreen({ name: 'profile', contactId: contact.id })}
          >
            <div className="avatar sm" style={{ background: contact.color }}>
              {initials(contact.name)}
            </div>
            <div className="row-main">
              <div className="row-title">
                <span>{contact.name}</span>
              </div>
              <div className="row-sub" style={{ color: 'rgba(255,255,255,0.85)' }}>
                <span>{contact.online ? 'в сети' : contact.lastSeen ?? 'был(а) недавно'}</span>
              </div>
            </div>
          </button>
          {visual.visualGiftsEnabled && (
            <button
              className="icon-btn"
              title="Подарок"
              onClick={() => setScreen({ name: 'gifts', contactId: contact.id })}
            >
              🎁
            </button>
          )}
        </div>
        <div className="chat-bg">
          {chatMsgs.map((m) => (
            <div key={m.id} className={`bubble ${m.fromMe ? 'out' : 'in'}`}>
              <div>{m.text}</div>
              <div className="meta">{m.time}</div>
            </div>
          ))}
        </div>
        <div className="composer">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Сообщение"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && draft.trim()) {
                const now = new Date()
                const time = `${now.getHours().toString().padStart(2, '0')}:${now
                  .getMinutes()
                  .toString()
                  .padStart(2, '0')}`
                const text = draft.trim()
                setMsgs((prev) => [
                  ...prev,
                  {
                    id: `local-${Date.now()}`,
                    chatId: chat.id,
                    fromMe: true,
                    text,
                    time,
                  },
                ])
                touchChat(chat.id, text, time)
                setDraft('')
              }
            }}
          />
          <button
            className="send-fab"
            aria-label="Отправить"
            onClick={() => {
              if (!draft.trim()) return
              const now = new Date()
              const time = `${now.getHours().toString().padStart(2, '0')}:${now
                .getMinutes()
                .toString()
                .padStart(2, '0')}`
              const text = draft.trim()
              setMsgs((prev) => [
                ...prev,
                {
                  id: `local-${Date.now()}`,
                  chatId: chat.id,
                  fromMe: true,
                  text,
                  time,
                },
              ])
              touchChat(chat.id, text, time)
              setDraft('')
            }}
          >
            <SendIcon />
          </button>
        </div>
      </div>
    )
  }

  if (screen.name === 'profile') {
    const contact = contacts.find((c) => c.id === screen.contactId)!
    body = (
      <div className="screen" key={`profile-${contact.id}`}>
        <div className="topbar">
          <button
            className="icon-btn"
            onClick={() => {
              const chat = chatList.find((c) => c.contactId === contact.id)
              if (chat) setScreen({ name: 'chat', chatId: chat.id })
              else setScreen({ name: 'chats' })
            }}
          >
            <BackIcon />
          </button>
          <h1>Профиль</h1>
        </div>
        <div className="scroll-body">
          <div className="profile-hero">
            <div className="avatar lg" style={{ background: contact.color }}>
              {initials(contact.name)}
            </div>
            <h2>{contact.name}</h2>
            <p>@{contact.username}</p>
            <p>{contact.online ? 'в сети' : contact.lastSeen}</p>
          </div>
          <div className="card-block" style={{ marginTop: -12 }}>
            {visual.visualGiftsEnabled && (
              <button
                className="action-row"
                onClick={() => setScreen({ name: 'gifts', contactId: contact.id })}
              >
                <div className="avatar sm" style={{ background: '#e17055' }}>
                  🎁
                </div>
                <div className="row-main">
                  <div className="row-title">
                    <span>Отправить подарок</span>
                  </div>
                  <div className="row-sub">
                    <span>Визуальный подарок через MonkeyGram</span>
                  </div>
                </div>
              </button>
            )}
            <div className="action-row" style={{ cursor: 'default' }}>
              <div className="row-main">
                <div className="row-title">
                  <span>О себе</span>
                </div>
                <div className="row-sub">
                  <span>{contact.bio}</span>
                </div>
              </div>
            </div>
          </div>
          {!visual.visualGiftsEnabled && (
            <p className="hint">
              Кнопка «Отправить подарок» появится после включения визуалки в Настройки → MonkeyGram.
            </p>
          )}
        </div>
      </div>
    )
  }

  if (screen.name === 'settings') {
    body = (
      <div className="screen" key="settings">
        <div className="topbar">
          <button className="icon-btn" onClick={() => setScreen({ name: 'chats' })}>
            <BackIcon />
          </button>
          <h1>Настройки</h1>
        </div>
        <div className="scroll-body">
          <div className="profile-hero" style={{ paddingBottom: 22 }}>
            <div className="avatar lg" style={{ background: '#2481cc' }}>
              🐵
            </div>
            <h2>{ME.name}</h2>
            <p>@{ME.username}</p>
          </div>
          <div className="section-label">MonkeyGram</div>
          <div className="card-block">
            <button className="setting-row" onClick={openMonkeygram}>
              <div className="avatar sm" style={{ background: 'linear-gradient(145deg,#ffd56a,#e17055)' }}>
                ✨
              </div>
              <div className="row-main">
                <div className="row-title">
                  <span>Визуальные функции</span>
                </div>
                <div className="row-sub">
                  <span>Подарки, Stars, TON · только визуально</span>
                </div>
              </div>
            </button>
            <button className="setting-row" onClick={() => setScreen({ name: 'wallet' })}>
              <div className="avatar sm" style={{ background: '#f5a623' }}>
                ★
              </div>
              <div className="row-main">
                <div className="row-title">
                  <span>Кошелёк</span>
                </div>
                <div className="row-sub">
                  <span>
                    {visual.visualBalanceEnabled
                      ? `${formatAmount(visual.starsBalance, 'stars')} ★ · ${formatAmount(visual.tonBalance, 'ton')} TON`
                      : 'Баланс выключен'}
                  </span>
                </div>
              </div>
            </button>
            <button className="setting-row" onClick={() => setScreen({ name: 'gifts' })}>
              <div className="avatar sm" style={{ background: '#6c5ce7' }}>
                💎
              </div>
              <div className="row-main">
                <div className="row-title">
                  <span>Витрина подарков и NFT</span>
                </div>
                <div className="row-sub">
                  <span>Покупка за визуальные Stars / TON</span>
                </div>
              </div>
            </button>
          </div>
          <div className="section-label">Аккаунт</div>
          <div className="card-block">
            <div className="setting-row" style={{ cursor: 'default' }}>
              <div className="row-main">
                <div className="row-title">
                  <span>Номер</span>
                </div>
                <div className="row-sub">
                  <span>{ME.phone}</span>
                </div>
              </div>
            </div>
            <div className="setting-row" style={{ cursor: 'default' }}>
              <div className="row-main">
                <div className="row-title">
                  <span>Имя пользователя</span>
                </div>
                <div className="row-sub">
                  <span>@{ME.username}</span>
                </div>
              </div>
            </div>
          </div>
          <p className="hint">MonkeyGram — демо-клиент. Реальные платежи Telegram не выполняются.</p>
        </div>
      </div>
    )
  }

  if (screen.name === 'monkeygram') {
    body = (
      <div className="screen" key="monkeygram">
        <div className="topbar">
          <button className="icon-btn" onClick={() => setScreen({ name: 'settings' })}>
            <BackIcon />
          </button>
          <h1>Визуальные функции</h1>
        </div>
        <div className="scroll-body">
          <div className="section-label">Подарки</div>
          <div className="card-block">
            <div className="setting-row" style={{ cursor: 'default' }}>
              <div className="row-main">
                <div className="row-title">
                  <span>Включить визуалку</span>
                </div>
                <div className="row-sub">
                  <span>Кнопка «Отправить подарок» в профиле</span>
                </div>
              </div>
              <button
                className={`toggle ${visual.visualGiftsEnabled ? 'on' : ''}`}
                aria-pressed={visual.visualGiftsEnabled}
                onClick={() => setVisualGiftsEnabled(!visual.visualGiftsEnabled)}
              >
                <span />
              </button>
            </div>
          </div>

          <div className="section-label">Балансы</div>
          <div className="card-block">
            <div className="setting-row" style={{ cursor: 'default' }}>
              <div className="row-main">
                <div className="row-title">
                  <span>Включить баланс</span>
                </div>
                <div className="row-sub">
                  <span>Визуальные Stars и TON</span>
                </div>
              </div>
              <button
                className={`toggle ${visual.visualBalanceEnabled ? 'on' : ''}`}
                aria-pressed={visual.visualBalanceEnabled}
                onClick={() => setVisualBalanceEnabled(!visual.visualBalanceEnabled)}
              >
                <span />
              </button>
            </div>

            {visual.visualBalanceEnabled && (
              <>
                <div className="field">
                  <label htmlFor="stars">Баланс Stars</label>
                  <input
                    id="stars"
                    inputMode="decimal"
                    value={starsInput}
                    onChange={(e) => setStarsInput(e.target.value)}
                    placeholder="0"
                  />
                </div>
                <div className="field">
                  <label htmlFor="ton">Баланс TON</label>
                  <input
                    id="ton"
                    inputMode="decimal"
                    value={tonInput}
                    onChange={(e) => setTonInput(e.target.value)}
                    placeholder="0"
                  />
                </div>
                <div style={{ padding: '4px 14px 14px' }}>
                  <button className="primary-btn" onClick={saveVisualBalances}>
                    Сохранить балансы
                  </button>
                </div>
              </>
            )}
          </div>
          <p className="hint">
            Балансы хранятся локально в браузере и не сбрасываются после перезагрузки. Пополнения и
            траты появляются в историях Stars и TON.
          </p>
          <div style={{ padding: '0 12px 16px', display: 'grid', gap: 8 }}>
            <button className="secondary-btn" onClick={() => setScreen({ name: 'history', currency: 'stars' })}>
              История Stars
            </button>
            <button className="secondary-btn" onClick={() => setScreen({ name: 'history', currency: 'ton' })}>
              История TON
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (screen.name === 'wallet') {
    body = (
      <div className="screen" key="wallet">
        <div className="topbar">
          <button className="icon-btn" onClick={() => setScreen({ name: 'settings' })}>
            <BackIcon />
          </button>
          <h1>Кошелёк</h1>
        </div>
        <div className="scroll-body white">
          {!visual.visualBalanceEnabled ? (
            <div className="empty">
              Визуальный баланс выключен.
              <div style={{ marginTop: 12 }}>
                <button className="primary-btn" onClick={openMonkeygram}>
                  Открыть MonkeyGram
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="balance-pills">
                <button className="pill stars" onClick={() => setScreen({ name: 'history', currency: 'stars' })}>
                  <div className="label">Telegram Stars</div>
                  <div className="value">{formatAmount(visual.starsBalance, 'stars')}</div>
                </button>
                <button className="pill ton" onClick={() => setScreen({ name: 'history', currency: 'ton' })}>
                  <div className="label">TON</div>
                  <div className="value">{formatAmount(visual.tonBalance, 'ton')}</div>
                </button>
              </div>
              <div className="card-block">
                <button className="setting-row" onClick={() => setScreen({ name: 'gifts' })}>
                  <div className="row-main">
                    <div className="row-title">
                      <span>Купить подарок / NFT</span>
                    </div>
                    <div className="row-sub">
                      <span>Списание с визуального баланса</span>
                    </div>
                  </div>
                </button>
                <button className="setting-row" onClick={openMonkeygram}>
                  <div className="row-main">
                    <div className="row-title">
                      <span>Изменить балансы</span>
                    </div>
                    <div className="row-sub">
                      <span>Пополнение сохранится в истории</span>
                    </div>
                  </div>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  if (screen.name === 'gifts') {
    const contact = screen.contactId ? contacts.find((c) => c.id === screen.contactId) : undefined
    const list = gifts.filter((g) => g.kind === giftTab)

    body = (
      <div className="screen" key="gifts">
        <div className="topbar">
          <button
            className="icon-btn"
            onClick={() => {
              if (contact) setScreen({ name: 'profile', contactId: contact.id })
              else setScreen({ name: 'settings' })
            }}
          >
            <BackIcon />
          </button>
          <h1>{contact ? 'Отправить подарок' : 'Витрина'}</h1>
        </div>
        <div className="scroll-body white">
          {visual.visualBalanceEnabled && (
            <div className="balance-pills">
              <div className="pill stars">
                <div className="label">Stars</div>
                <div className="value">{formatAmount(visual.starsBalance, 'stars')}</div>
              </div>
              <div className="pill ton">
                <div className="label">TON</div>
                <div className="value">{formatAmount(visual.tonBalance, 'ton')}</div>
              </div>
            </div>
          )}
          <div className="tabs">
            <button className={`tab ${giftTab === 'gift' ? 'active' : ''}`} onClick={() => setGiftTab('gift')}>
              Подарки
            </button>
            <button className={`tab ${giftTab === 'nft' ? 'active' : ''}`} onClick={() => setGiftTab('nft')}>
              NFT
            </button>
          </div>
          <div className="gift-grid">
            {list.map((item) => (
              <button
                key={item.id}
                className="gift-card"
                style={{ background: item.gradient }}
                onClick={() => buyOrSend(item, contact)}
              >
                <div>
                  {item.limited && <span className="tag">Limited</span>}
                  <div className="emoji">{item.emoji}</div>
                </div>
                <div>
                  <div className="name">{item.name}</div>
                  <div className="price">
                    {item.priceTon != null
                      ? `${formatAmount(item.priceTon, 'ton')} TON`
                      : `${formatAmount(item.priceStars ?? 0, 'stars')} Stars`}
                  </div>
                </div>
              </button>
            ))}
          </div>
          {contact && !visual.visualGiftsEnabled && (
            <p className="hint">Включите визуалку в настройках MonkeyGram, чтобы дарить подарки.</p>
          )}
        </div>
      </div>
    )
  }

  if (screen.name === 'history') {
    const entries = historyFor(screen.currency)
    body = (
      <div className="screen" key={`history-${screen.currency}`}>
        <div className="topbar">
          <button className="icon-btn" onClick={() => setScreen({ name: 'wallet' })}>
            <BackIcon />
          </button>
          <h1>{screen.currency === 'stars' ? 'История Stars' : 'История TON'}</h1>
        </div>
        <div className="scroll-body white">
          {entries.length === 0 ? (
            <div className="empty">Пока нет операций. Пополните баланс или купите NFT/подарок.</div>
          ) : (
            entries.map((e) => {
              const date = new Date(e.at)
              const when = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Europe/Moscow',
              })
              return (
                <div key={e.id} className="history-row">
                  <div
                    className="avatar sm"
                    style={{ background: e.currency === 'stars' ? '#f5a623' : '#0098ea' }}
                  >
                    {e.currency === 'stars' ? '★' : '💎'}
                  </div>
                  <div className="row-main">
                    <div className="row-title">
                      <span>{e.title}</span>
                      <span className={`history-amount ${e.direction}`}>
                        {e.direction === 'in' ? '+' : '−'}
                        {formatAmount(e.amount, e.currency)}
                      </span>
                    </div>
                    <div className="row-sub">
                      <span>{e.subtitle ?? when}</span>
                      <span className="time">{when}</span>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <div className="phone">
        {body}
        {toast && <div className="toast">{toast}</div>}
      </div>
    </div>
  )
}
