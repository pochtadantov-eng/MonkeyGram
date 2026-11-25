export type Contact = {
  id: string
  name: string
  username: string
  bio: string
  color: string
  online: boolean
  lastSeen?: string
}

export type Chat = {
  id: string
  contactId: string
  lastMessage: string
  time: string
  unread: number
  pinned?: boolean
}

export type Message = {
  id: string
  chatId: string
  fromMe: boolean
  text: string
  time: string
}

export type GiftItem = {
  id: string
  name: string
  emoji: string
  gradient: string
  priceStars?: number
  priceTon?: number
  kind: 'gift' | 'nft'
  limited?: boolean
}

export const ME = {
  name: 'MonkeyGram',
  username: 'monkeygram',
  bio: 'Визуальный клиент · только для игры',
  phone: '+7 900 000-00-00',
}

export const contacts: Contact[] = [
  {
    id: 'c1',
    name: 'Анна Козлова',
    username: 'anna_k',
    bio: 'Дизайн и кофе ☕',
    color: '#e17055',
    online: true,
  },
  {
    id: 'c2',
    name: 'Игорь Волков',
    username: 'ivolkov',
    bio: 'TON · NFT · стартапы',
    color: '#6c5ce7',
    online: false,
    lastSeen: 'был(а) недавно',
  },
  {
    id: 'c3',
    name: 'Мария',
    username: 'maria_sun',
    bio: 'Путешествия',
    color: '#00b894',
    online: true,
  },
  {
    id: 'c4',
    name: 'Telegram News',
    username: 'telegram',
    bio: 'Official Telegram channel',
    color: '#0984e3',
    online: false,
    lastSeen: 'канал',
  },
  {
    id: 'c5',
    name: 'Денис',
    username: 'denis_dev',
    bio: 'Building things',
    color: '#fdcb6e',
    online: false,
    lastSeen: 'был(а) в 14:20',
  },
]

export const chats: Chat[] = [
  {
    id: 'ch1',
    contactId: 'c1',
    lastMessage: 'Ок, давай вечером!',
    time: '18:42',
    unread: 2,
    pinned: true,
  },
  {
    id: 'ch2',
    contactId: 'c2',
    lastMessage: 'Посмотри новый дроп',
    time: '16:11',
    unread: 0,
  },
  {
    id: 'ch3',
    contactId: 'c3',
    lastMessage: 'Фото с моря 🌊',
    time: 'вчера',
    unread: 1,
  },
  {
    id: 'ch4',
    contactId: 'c4',
    lastMessage: 'Telegram Premium updates',
    time: 'пн',
    unread: 0,
  },
  {
    id: 'ch5',
    contactId: 'c5',
    lastMessage: 'Скинул ссылку',
    time: 'вс',
    unread: 0,
  },
]

export const messages: Message[] = [
  { id: 'm1', chatId: 'ch1', fromMe: false, text: 'Привет! Как дела?', time: '18:30' },
  { id: 'm2', chatId: 'ch1', fromMe: true, text: 'Привет! Всё отлично 👋', time: '18:32' },
  { id: 'm3', chatId: 'ch1', fromMe: false, text: 'Сходишь на кофе?', time: '18:40' },
  { id: 'm4', chatId: 'ch1', fromMe: false, text: 'Ок, давай вечером!', time: '18:42' },
  { id: 'm5', chatId: 'ch2', fromMe: false, text: 'Видел коллекцию на Fragment?', time: '15:50' },
  { id: 'm6', chatId: 'ch2', fromMe: true, text: 'Ещё смотрю', time: '16:00' },
  { id: 'm7', chatId: 'ch2', fromMe: false, text: 'Посмотри новый дроп', time: '16:11' },
  { id: 'm8', chatId: 'ch3', fromMe: false, text: 'Фото с моря 🌊', time: '10:12' },
  { id: 'm9', chatId: 'ch4', fromMe: false, text: 'Telegram Premium updates', time: '09:00' },
  { id: 'm10', chatId: 'ch5', fromMe: true, text: 'Готов релиз?', time: 'вс' },
  { id: 'm11', chatId: 'ch5', fromMe: false, text: 'Скинул ссылку', time: 'вс' },
]

export const gifts: GiftItem[] = [
  {
    id: 'g1',
    name: 'Голубая звезда',
    emoji: '⭐',
    gradient: 'linear-gradient(145deg,#74b9ff,#0984e3)',
    priceStars: 50,
    kind: 'gift',
  },
  {
    id: 'g2',
    name: 'Сердце',
    emoji: '💙',
    gradient: 'linear-gradient(145deg,#ff7675,#e84393)',
    priceStars: 25,
    kind: 'gift',
  },
  {
    id: 'g3',
    name: 'Торт',
    emoji: '🎂',
    gradient: 'linear-gradient(145deg,#ffeaa7,#fdcb6e)',
    priceStars: 100,
    kind: 'gift',
  },
  {
    id: 'g4',
    name: 'Ракета',
    emoji: '🚀',
    gradient: 'linear-gradient(145deg,#a29bfe,#6c5ce7)',
    priceStars: 150,
    kind: 'gift',
  },
  {
    id: 'n1',
    name: 'Monkey Crown',
    emoji: '👑',
    gradient: 'linear-gradient(145deg,#fdcb6e,#e17055)',
    priceTon: 2.5,
    kind: 'nft',
    limited: true,
  },
  {
    id: 'n2',
    name: 'Neon Banana',
    emoji: '🍌',
    gradient: 'linear-gradient(145deg,#55efc4,#00b894)',
    priceTon: 1.2,
    kind: 'nft',
    limited: true,
  },
  {
    id: 'n3',
    name: 'Pixel Pepe',
    emoji: '🐸',
    gradient: 'linear-gradient(145deg,#81ecec,#00cec9)',
    priceStars: 500,
    kind: 'nft',
  },
  {
    id: 'n4',
    name: 'Crystal Gift',
    emoji: '💎',
    gradient: 'linear-gradient(145deg,#dfe6e9,#74b9ff)',
    priceTon: 5,
    kind: 'nft',
    limited: true,
  },
]

export function contactById(id: string) {
  return contacts.find((c) => c.id === id)!
}

export function chatById(id: string) {
  return chats.find((c) => c.id === id)!
}
