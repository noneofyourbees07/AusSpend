import styles from './Scope.module.css';

const REVENUE_BY_LEVEL = [
  {
    level: 'Federal (Commonwealth)',
    color: '#58a6ff',
    intro: 'Collected by the ATO and remitted to the Commonwealth. This is what AusSpend currently tracks.',
    inScope: true,
    items: [
      { name: 'Income Tax — Individuals',     amount: '~$320B', note: 'PAYG withholding + tax returns' },
      { name: 'Income Tax — Companies',       amount: '~$110B', note: 'Corporate tax on profits' },
      { name: 'GST',                          amount: '~$90B',  note: 'Collected federally, distributed to states' },
      { name: 'Fuel Excise',                  amount: '~$20B',  note: 'On petrol & diesel sales' },
      { name: 'Tobacco Excise',               amount: '~$12B',  note: 'On cigarettes & tobacco' },
      { name: 'Alcohol Excise',               amount: '~$7B',   note: 'On beer, wine, spirits' },
      { name: 'Customs Duty',                 amount: '~$2B',   note: 'On imports' },
      { name: 'Income Tax — Superannuation',  amount: '~$15B',  note: 'On super fund earnings' },
      { name: 'Fringe Benefits Tax',          amount: '~$5B',   note: 'On employer-provided benefits' },
      { name: 'Petroleum Resource Rent Tax',  amount: '~$2B',   note: 'On offshore oil/gas' },
      { name: 'Non-Tax Revenue',              amount: '~$36B',  note: 'Interest, dividends, fees, asset sales' },
    ],
  },
  {
    level: 'State / Territory',
    color: '#d29922',
    intro: '8 states & territories each collect their own taxes. AusSpend does NOT yet show these — each state Treasury publishes its own Budget Papers.',
    inScope: false,
    items: [
      { name: 'Vehicle Registration (rego)',  amount: 'varies',  note: 'Cars, trucks, motorcycles — paid annually' },
      { name: 'Driver Licence Fees',          amount: 'varies',  note: 'Renewals, learner permits, photo cards' },
      { name: 'Stamp Duty — Property',        amount: 'large',   note: 'On house & land purchases' },
      { name: 'Stamp Duty — Motor Vehicle',   amount: 'large',   note: 'On new & used car purchases' },
      { name: 'Land Tax',                     amount: 'large',   note: 'Annual tax on land value (excluding family home in most states)' },
      { name: 'Payroll Tax',                  amount: 'large',   note: 'Charged to employers above a threshold' },
      { name: 'Gambling Taxes',               amount: 'medium',  note: 'Pokies, casinos, racing, lotteries' },
      { name: 'Insurance Duty',               amount: 'medium',  note: 'On most insurance premiums' },
      { name: 'Mining Royalties',             amount: 'large',   note: 'Especially in WA, QLD, NSW' },
      { name: 'GST distribution from federal',amount: 'shared',  note: 'States receive a slice of federal GST collections' },
    ],
  },
  {
    level: 'Local (Council)',
    color: '#3fb950',
    intro: '~537 local councils across Australia. AusSpend does NOT track these — each council publishes its own annual report.',
    inScope: false,
    items: [
      { name: 'Council Rates',                amount: 'varies', note: 'Annual property-based charge — main income source for councils' },
      { name: 'Waste / Bin Collection Fees',  amount: 'varies', note: 'Sometimes part of rates, sometimes separate' },
      { name: 'Building & Planning Permits',  amount: 'small',  note: 'Development approval fees' },
      { name: 'Parking Fees & Fines',         amount: 'small',  note: 'Meters, residential permits, infringements' },
      { name: 'Animal Registration',          amount: 'small',  note: 'Dog/cat registration' },
      { name: 'Library/Pool/Facility Fees',   amount: 'small',  note: 'Recreation centre membership, room hire' },
      { name: 'Federal & State Grants',       amount: 'large',  note: 'Roads to Recovery, Financial Assistance Grants, etc.' },
    ],
  },
];

export default function Scope() {
  return (
    <div className={styles.page}>

      {/* Intro */}
      <div className={styles.intro}>
        <h2 className={styles.heading}>Data Scope &amp; Limitations</h2>
        <p className={styles.sub}>
          Australia has <strong>three levels of government</strong>, each with their own
          taxes and budgets. This page explains what AusSpend tracks and what it doesn&rsquo;t —
          so you know exactly what the numbers cover.
        </p>
      </div>

      {/* The 3 levels */}
      <div className={styles.levels}>
        {REVENUE_BY_LEVEL.map(level => (
          <div key={level.level} className={styles.levelCard}>
            <div className={styles.levelHead} style={{ borderLeftColor: level.color }}>
              <h3 className={styles.levelTitle}>{level.level}</h3>
              <span className={`${styles.badge} ${level.inScope ? styles.badgeIn : styles.badgeOut}`}>
                {level.inScope ? 'Tracked' : 'Not tracked'}
              </span>
            </div>
            <p className={styles.levelIntro}>{level.intro}</p>
            <ul className={styles.itemList}>
              {level.items.map(item => (
                <li key={item.name} className={styles.item}>
                  <div className={styles.itemHeader}>
                    <span className={styles.itemName}>{item.name}</span>
                    <span className={styles.itemAmount}>{item.amount}</span>
                  </div>
                  <span className={styles.itemNote}>{item.note}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Why federal only */}
      <div className={styles.note}>
        <h3 className={styles.noteTitle}>Why federal only (for now)?</h3>
        <p>
          State and local government data is published, but it&rsquo;s spread across
          dozens of websites in different formats. Each of the 8 states publishes its
          own Budget Papers, and each of the ~537 councils publishes its own annual
          report. Building a unified state/local view is the next step — but it requires
          ingesting data from a much wider set of sources.
        </p>
        <p>
          For now, AusSpend focuses on the <strong>federal</strong> picture because:
        </p>
        <ul className={styles.bulletList}>
          <li>Federal is by far the largest level (~$700B/year vs ~$350B combined state/local)</li>
          <li>Federal collects GST and distributes most of it to states — so federal data captures a lot of indirect activity</li>
          <li>Federal data is the most consistently published (Budget Papers, AOFM, ATO statistics)</li>
        </ul>
      </div>

      {/* What's missing from federal too */}
      <div className={styles.note}>
        <h3 className={styles.noteTitle}>Even within federal, what&rsquo;s incomplete</h3>
        <ul className={styles.bulletList}>
          <li><strong>Recent contract detail (2020-onwards):</strong> AusTender exports on data.gov.au stopped updating in 2019. The live AusTender system blocks automated tools. We can show high-level Budget Paper figures but not individual contracts.</li>
          <li><strong>Grants register:</strong> The GrantConnect system has every federal grant ever awarded but only as searchable web pages, not bulk downloads.</li>
          <li><strong>Procurement under $10K:</strong> AusTender only includes contracts ≥$10,000.</li>
          <li><strong>Off-budget vehicles:</strong> NBN Co, Future Fund, Inland Rail Co. — these have separate accounts not always rolled into headline budget figures.</li>
        </ul>
      </div>
    </div>
  );
}
