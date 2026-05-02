import { useState, useEffect, useRef } from 'react'

const API = 'http://localhost:8000'

/* ── Real icon URLs from icons8 CDN ── */
const ICONS = {
  nfc: 'https://img.icons8.com/ios-filled/50/ffffff/nfc-sign.png',
  coin: 'https://img.icons8.com/3d-fluency/94/coin-wallet.png',
  homeActive: 'https://img.icons8.com/ios-filled/50/1B8EF8/home--v1.png',
  home: 'https://img.icons8.com/ios/50/9CA3AF/home--v1.png',
  cardActive: 'https://img.icons8.com/ios-filled/50/1B8EF8/bank-card-back-side--v1.png',
  card: 'https://img.icons8.com/ios/50/9CA3AF/bank-card-back-side--v1.png',
  profileActive: 'https://img.icons8.com/ios-filled/50/1B8EF8/user-male-circle--v1.png',
  profile: 'https://img.icons8.com/ios/50/9CA3AF/user-male-circle--v1.png',
  coffee: 'https://img.icons8.com/color/96/coffee-to-go.png',
  mcdonalds: 'https://img.icons8.com/color/96/mcdonalds.png',
  book: 'https://img.icons8.com/color/96/book-shelf.png',
  bakery: 'https://img.icons8.com/color/96/bread.png',
  lemon: 'https://img.icons8.com/color/96/lemon.png',
  market: 'https://img.icons8.com/color/96/shopping-cart.png',
}

const PARTNER_ICON_MAP = {
  "Coffee Station": ICONS.coffee,
  "McDonald's": ICONS.mcdonalds,
  "Baku Book Center": ICONS.book,
  "Çörək Evi": ICONS.bakery,
  "Limon Lounge": ICONS.lemon,
  "Bravo Market": ICONS.market,
}

/* ── Smart image with fallback ── */
function Img({ src, fallback, alt, style }) {
  const [err, setErr] = useState(false)
  if (err) {
    return (
      <div style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1E2D40', borderRadius: 8, fontSize: 14, color: '#fff', fontWeight: 700 }}>
        {fallback}
      </div>
    )
  }
  return <img src={src} alt={alt || ''} style={style} onError={() => setErr(true)} draggable={false} />
}

/* ── Colors (Purple + White theme) ── */
const C = {
  bg: '#F5F0FF',
  surface: '#FFFFFF',
  border: '#E8E0F0',
  purple: '#6C3FC5',
  purpleDark: '#4A2D8A',
  purpleLight: '#EDE5FF',
  purpleMuted: '#B8A0D8',
  blue: '#6C3FC5',
  gold: '#E8A910',
  green: '#22C07A',
  greenBg: '#E8F8F0',
  muted: '#8B7DA0',
  white: '#FFFFFF',
  text: '#1A0A2E',
  textMuted: '#6B5F7B',
}

/* BakiKart official card image */
const BAKIKART_IMG = '/bakikart.png'

/* Baku Metro colorful train icon (inline SVG) */
const MetroTrainIcon = ({ size = 34 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="100" height="100" rx="22" fill="#FFFFFF"/>
    {/* Rails */}
    <line x1="18" y1="82" x2="55" y2="44" stroke="#555" strokeWidth="3"/>
    <line x1="25" y1="82" x2="62" y2="44" stroke="#555" strokeWidth="3"/>
    {/* Cross ties */}
    <line x1="22" y1="76" x2="34" y2="76" stroke="#555" strokeWidth="2.5"/>
    <line x1="28" y1="70" x2="40" y2="70" stroke="#555" strokeWidth="2.5"/>
    <line x1="34" y1="64" x2="46" y2="64" stroke="#555" strokeWidth="2.5"/>
    <line x1="40" y1="58" x2="52" y2="58" stroke="#555" strokeWidth="2.5"/>
    {/* Train body */}
    <rect x="35" y="22" width="42" height="48" rx="10" fill="url(#trainGrad)"/>
    {/* Windows */}
    <rect x="41" y="30" width="12" height="16" rx="3" fill="#E8F4FF" opacity="0.9"/>
    <rect x="58" y="30" width="12" height="16" rx="3" fill="#E8F4FF" opacity="0.9"/>
    {/* Speed lines */}
    <line x1="20" y1="32" x2="34" y2="32" stroke="#FFD700" strokeWidth="2.5" strokeLinecap="round"/>
    <line x1="15" y1="38" x2="32" y2="38" stroke="#00BFFF" strokeWidth="2" strokeLinecap="round"/>
    <line x1="18" y1="44" x2="34" y2="44" stroke="#FFD700" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
    {/* Headlight */}
    <rect x="41" y="52" width="30" height="6" rx="3" fill="#222"/>
    <defs>
      <linearGradient id="trainGrad" x1="35" y1="22" x2="77" y2="70">
        <stop offset="0%" stopColor="#00BFFF"/>
        <stop offset="35%" stopColor="#8B5CF6"/>
        <stop offset="65%" stopColor="#EF4444"/>
        <stop offset="100%" stopColor="#22C55E"/>
      </linearGradient>
    </defs>
  </svg>
)

/* ── Time formatting helpers ── */
function fmtTime(h, m) { return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}` }
function fmtAMPM(h, m) {
  const ampm = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${String(h12).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm}`
}
function addMins(h, m, add) {
  const total = h * 60 + m + add
  return [Math.floor(total / 60) % 24, total % 60]
}

/* ══════════════════════════════════════════════════════════════════
   MAIN APP COMPONENT
   ══════════════════════════════════════════════════════════════════ */
export default function App() {
  const [stations, setStations] = useState([])
  const [station, setStation] = useState('28-May')
  const [waitMin, setWaitMin] = useState(0)
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState(0)
  const debounceRef = useRef(null)

  const [baseHour, setBaseHour] = useState(8)
  const [baseMinute, setBaseMinute] = useState(30)

  /* load stations from API */
  useEffect(() => {
    fetch(`${API}/stations`)
      .then(r => r.json())
      .then(d => setStations(d.stations))
      .catch(() => setStations(['28-May', 'Sahil', 'Icherisheher', 'Ganjlik', 'Koroghlu', 'Nariman Narimanov', 'Ulduz', 'Hazi Aslanov']))
  }, [])

  /* fetch prediction from ML model */
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setLoading(true)
      fetch(`${API}/predict-reward`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station, hour: baseHour, minute: baseMinute, added_minutes: waitMin }),
      })
        .then(r => r.json())
        .then(d => { setPrediction(d); setLoading(false) })
        .catch(() => setLoading(false))
    }, 150)
    return () => clearTimeout(debounceRef.current)
  }, [station, waitMin, baseHour, baseMinute])

  const coinsNow = prediction?.coins_now ?? 0
  const coinsWait = prediction?.coins_if_wait ?? 0
  const extraCoins = prediction?.extra_coins ?? 0
  const partners = prediction?.partners ?? []

  const [t15h, t15m] = addMins(baseHour, baseMinute, 15)
  const [t30h, t30m] = addMins(baseHour, baseMinute, 30)

  const waitSteps = [0, 15, 30]
  const progressPct = waitMin === 0 ? 0 : waitMin === 15 ? 50 : 100

  /* ── Inline Styles ── */
  const s = {
    phone: {
      width: 393, height: 852, borderRadius: 55, border: '10px solid #1a1a1a',
      boxShadow: '0 0 0 2px #333, 0 50px 100px rgba(0,0,0,.35)',
      overflow: 'hidden', position: 'relative', background: '#1a1a1a',
      display: 'flex', flexDirection: 'column',
    },
    island: {
      position: 'absolute', top: 8, left: '50%', transform: 'translateX(-50%)',
      width: 120, height: 34, background: '#1a1a1a', borderRadius: 20, zIndex: 60,
    },
    screen: {
      flex: 1, display: 'flex', flexDirection: 'column', borderRadius: 45,
      overflow: 'hidden', background: `linear-gradient(180deg, ${C.bg} 0%, #E8DFFF 40%, ${C.white} 100%)`,
    },
    scroll: {
      flex: 1, overflowY: 'auto', overflowX: 'hidden', WebkitOverflowScrolling: 'touch',
      scrollbarWidth: 'none',
    },
    statusBar: {
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '52px 28px 8px',
    },
    header: {
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '4px 20px 12px',
    },
    content: { padding: '0 16px 24px' },
    bakikart: {
      borderRadius: 20, position: 'relative', overflow: 'hidden',
      boxShadow: '0 8px 32px rgba(108,63,197,.25)', marginBottom: 14,
    },
    section: {
      background: C.surface, borderRadius: 20, padding: 20, marginBottom: 14,
      border: `1px solid ${C.border}`, boxShadow: '0 2px 12px rgba(108,63,197,.08)',
    },
    earningsCard: {
      background: C.greenBg, borderRadius: 20, padding: 20, marginBottom: 14,
      border: '1px solid #C8E8D8', boxShadow: '0 2px 12px rgba(34,192,122,.1)',
    },
    bottomNav: {
      display: 'flex', justifyContent: 'space-around', alignItems: 'center',
      padding: '10px 0 24px', background: C.white, borderTop: `1px solid ${C.border}`,
      flexShrink: 0,
    },
    tabBtn: (active) => ({
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
      background: 'none', border: 'none', cursor: 'pointer', padding: '4px 12px',
    }),
    tabLabel: (active) => ({
      fontSize: 10, fontWeight: active ? 600 : 500,
      color: active ? C.blue : C.muted,
    }),
    timelineDot: (isActive, isPassed) => ({
      width: 14, height: 14, borderRadius: '50%',
      border: `3px solid ${isActive || isPassed ? C.purple : '#D4CBE5'}`,
      background: isActive ? C.purple : C.white,
      cursor: 'pointer', position: 'relative', zIndex: 2, padding: 0,
    }),
    pillBtn: (selected) => ({
      background: selected ? C.purple : C.surface,
      color: selected ? '#fff' : C.muted,
      border: selected ? 'none' : `1px solid ${C.border}`,
      borderRadius: 20, padding: '6px 16px', fontSize: 12, fontWeight: 700,
      cursor: 'pointer', transition: 'all .2s',
    }),
    partnerCard: {
      flexShrink: 0, width: 140, background: C.white, borderRadius: 16,
      padding: 14, border: `1px solid ${C.border}`, boxShadow: '0 2px 8px rgba(108,63,197,.06)',
    },
  }

  return (
    <div style={s.phone}>
      <div style={s.island} />
      <div style={s.screen}>

        {/* ── Scrollable area ── */}
        <div style={s.scroll}>

          {/* STATUS BAR */}
          <div style={s.statusBar}>
            <span style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{fmtAMPM(baseHour, baseMinute)}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <svg width="16" height="16" fill={C.text} viewBox="0 0 24 24"><path d="M2 17h2v4H2zm4-5h2v9H6zm4-4h2v13h-2zm4-3h2v16h-2zm4-2h2v18h-2z"/></svg>
              <svg width="16" height="16" fill={C.text} viewBox="0 0 24 24"><path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9zm8 8l3 3 3-3a4.24 4.24 0 00-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z"/></svg>
              <div style={{ width: 24, height: 11, border: `1.5px solid ${C.text}`, borderRadius: 3, position: 'relative', marginLeft: 2 }}>
                <div style={{ position: 'absolute', top: 1.5, left: 1.5, bottom: 1.5, width: '70%', background: C.text, borderRadius: 1.5 }} />
              </div>
            </div>
          </div>

          {/* HEADER */}
          <div style={s.header}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 38, height: 38, borderRadius: 12, overflow: 'hidden', boxShadow: '0 2px 8px rgba(108,63,197,.25)', flexShrink: 0 }}>
                <MetroTrainIcon size={38} />
              </div>
              <span style={{ fontSize: 20, fontWeight: 700, color: C.text, letterSpacing: -0.5 }}>Metron</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ fontSize: 12, color: C.muted }}>{station} Station</span>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.purple }} />
            </div>
          </div>

          <div style={s.content}>

            {/* ═══ BAKIKART (real card image) ═══ */}
            <div style={s.bakikart}>
              <img
                src={BAKIKART_IMG}
                alt="BakiKart"
                style={{ width: '100%', display: 'block', borderRadius: 20 }}
                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block' }}
              />
              {/* Fallback if image not found */}
              <div style={{ display: 'none', background: `linear-gradient(135deg, #1A9B8A, #0D7A6E)`, borderRadius: 20, padding: 20, minHeight: 180 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>BakiKart</span>
              </div>
              {/* Balance overlay */}
              <div style={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                background: 'linear-gradient(0deg, rgba(0,0,0,.65) 0%, rgba(0,0,0,.2) 60%, transparent 100%)',
                borderRadius: '0 0 20px 20px', padding: '28px 18px 14px',
              }}>
                <p style={{ fontSize: 10, color: 'rgba(255,255,255,.6)', margin: '0 0 2px' }}>Current Balance:</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 26, fontWeight: 700, color: '#fff' }}>120</span>
                  <Img src={ICONS.coin} fallback="M" alt="coin" style={{ width: 24, height: 24 }} />
                  <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Img src={ICONS.nfc} fallback="NFC" alt="NFC" style={{ width: 22, height: 22, opacity: 0.7 }} />
                  </div>
                </div>
              </div>
            </div>

            <p style={{ textAlign: 'center', fontSize: 13, color: '#4A5568', margin: '-4px 0 12px' }}>Hold Near Reader to Pay</p>

            {/* ═══ STATION & TIME — side by side ═══ */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>

              {/* Station card */}
              <div style={{ flex: 1, ...s.section, marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.purple} strokeWidth="2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  <span style={{ fontSize: 11, fontWeight: 600, color: C.muted }}>Station</span>
                </div>
                <select
                  value={station}
                  onChange={e => setStation(e.target.value)}
                  style={{
                    width: '100%', background: C.purpleLight, border: `1px solid ${C.border}`,
                    borderRadius: 10, padding: '10px 12px', fontSize: 13, fontWeight: 600, color: C.text,
                    fontFamily: 'Inter, sans-serif', outline: 'none', appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='%236C3FC5'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat', backgroundPosition: 'right 10px center',
                  }}
                >
                  {stations.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {/* Time card */}
              <div style={{ flex: 1, ...s.section, marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.purple} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  <span style={{ fontSize: 11, fontWeight: 600, color: C.muted }}>Time</span>
                </div>
                <input
                  type="time"
                  value={fmtTime(baseHour, baseMinute)}
                  onChange={e => {
                    const [h, m] = e.target.value.split(':').map(Number)
                    if (!isNaN(h) && !isNaN(m)) { setBaseHour(h); setBaseMinute(m) }
                  }}
                  style={{
                    width: '100%', background: C.purpleLight, border: `1px solid ${C.border}`,
                    borderRadius: 10, padding: '10px 12px', fontSize: 14, fontWeight: 600,
                    color: C.text, fontFamily: "'JetBrains Mono', monospace",
                    outline: 'none', textAlign: 'center',
                  }}
                />
              </div>
            </div>

            {/* ═══ WAIT PLANNER ═══ */}
            <div style={s.section}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <h2 style={{ fontSize: 16, fontWeight: 700, color: C.text, margin: 0 }}>Wait & Earn</h2>
                  <p style={{ fontSize: 12, color: C.muted, margin: 0 }}>Plan your wait for more coins</p>
                </div>
                <div style={s.pillBtn(true)}>
                  +{waitMin} min
                </div>
              </div>

              {/* Timeline dots */}
              <div style={{ position: 'relative', marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
                  {/* Track */}
                  <div style={{ position: 'absolute', left: 7, right: 7, top: '50%', transform: 'translateY(-50%)', height: 3, background: '#E0D6F0', borderRadius: 2 }}>
                    <div style={{ height: '100%', width: `${progressPct}%`, background: C.purple, borderRadius: 2, transition: 'width .3s' }} />
                  </div>
                  {waitSteps.map(w => (
                    <button
                      key={w}
                      onClick={() => setWaitMin(w)}
                      style={s.timelineDot(waitMin === w, w < waitMin)}
                    />
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                  <div style={{ textAlign: 'center', width: 70 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: C.text, margin: 0 }}>Now</p>
                    <p style={{ fontSize: 10, color: C.muted, margin: 0 }}>(0 min, {fmtTime(baseHour, baseMinute)})</p>
                  </div>
                  <div style={{ textAlign: 'center', width: 80 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: C.text, margin: 0 }}>+15 min</p>
                    <p style={{ fontSize: 10, color: C.muted, margin: 0 }}>({fmtAMPM(t15h, t15m)})</p>
                  </div>
                  <div style={{ textAlign: 'center', width: 70 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: C.text, margin: 0 }}>+30 min</p>
                    <p style={{ fontSize: 10, color: C.muted, margin: 0 }}>({fmtAMPM(t30h, t30m)})</p>
                  </div>
                </div>
              </div>
            </div>

            {/* ═══ PREDICTED EARNINGS ═══ */}
            <div style={s.earningsCard}>
              <p style={{ fontSize: 12, fontWeight: 600, color: C.green, marginBottom: 10 }}>Predicted Earnings</p>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontFamily: "'JetBrains Mono', monospace", fontSize: 42, fontWeight: 700,
                    color: C.green, lineHeight: 1,
                  }}>
                    +{waitMin === 0 ? coinsNow : coinsWait}
                  </span>
                  <Img src={ICONS.coin} fallback="M" alt="coin" style={{ width: 32, height: 32 }} />
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: 12, color: 'rgba(34,192,122,.7)', margin: 0, fontWeight: 500 }}>
                    {waitMin === 0 ? 'Current time' : `For waiting`}
                  </p>
                  {waitMin > 0 && (
                    <p style={{ fontSize: 12, color: 'rgba(34,192,122,.7)', margin: 0, fontWeight: 500 }}>
                      {waitMin} mins
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* ═══ SPEND YOUR WAIT ═══ */}
            <div style={{ marginBottom: 16 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: C.text, margin: '0 0 4px' }}>Spend Your Wait</h2>
              <p style={{ fontSize: 12, color: C.muted, margin: '0 0 12px' }}>Nearby Partners</p>

              <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8, scrollbarWidth: 'none' }}>
                {partners.length === 0 && (
                  <div style={{ width: '100%', textAlign: 'center', color: C.muted, fontSize: 13, padding: '24px 0' }}>
                    {loading ? 'Loading...' : 'Select a wait time to see offers'}
                  </div>
                )}
                {partners.map((p, i) => (
                  <div key={i} style={s.partnerCard}>
                    <Img
                      src={PARTNER_ICON_MAP[p.name] || ICONS.coffee}
                      fallback={p.icon}
                      alt={p.name}
                      style={{ width: 40, height: 40, marginBottom: 8, borderRadius: 10 }}
                    />
                    <p style={{ fontSize: 12, fontWeight: 700, color: C.text, margin: '0 0 2px', lineHeight: 1.3 }}>{p.name}</p>
                    <p style={{ fontSize: 10, color: C.muted, margin: '0 0 6px', lineHeight: 1.3 }}>{p.offer}</p>
                    <p style={{ fontSize: 9, color: '#4A5568', margin: 0, fontWeight: 500 }}>{p.distance}</p>
                  </div>
                ))}
              </div>
            </div>

          </div>{/* /content */}
        </div>{/* /scroll */}

        {/* ═══ BOTTOM TAB BAR ═══ */}
        <div style={s.bottomNav}>
          {[
            { label: 'Home', icon: ICONS.homeActive, iconOff: ICONS.home, fallback: 'H' },
            { label: 'Virtual Card', icon: ICONS.cardActive, iconOff: ICONS.card, fallback: 'C' },
            { label: 'Profile', icon: ICONS.profileActive, iconOff: ICONS.profile, fallback: 'P' },
          ].map((t, i) => (
            <button key={i} style={s.tabBtn(tab === i)} onClick={() => setTab(i)}>
              <Img
                src={tab === i ? t.icon : t.iconOff}
                fallback={t.fallback}
                alt={t.label}
                style={{ width: 24, height: 24 }}
              />
              <span style={s.tabLabel(tab === i)}>{t.label}</span>
            </button>
          ))}
        </div>

      </div>{/* /screen */}
    </div>
  )
}
