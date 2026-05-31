# V4 Next.js Drill-Down Modal Pattern

Adding interactive drill-down modals to Next.js (React) pages follows
a different pattern than the V3 Python `showXDetail()` JS functions.
This reference covers the React-specific approach.

## Pattern: `.map()` Arrow Function Body Conversion

When a `.map()` rendering needs to add local variables
(e.g. `const schedDisplay = ...`), the implicit-return arrow form
`jobs.map((job) => (` must be converted to a block body
`jobs.map((job) => {` with an explicit `return` statement.

### ❌ Wrong (crash on variable declaration)

```tsx
{items.map((item) => (
  const extra = compute(item);  // SyntaxError!
  <div key={item.id}>{extra}</div>
))}
```

### ✅ Correct (block body + return)

```tsx
{items.map((item) => {
  const extra = compute(item);
  return <div key={item.id}>{extra}</div>;
})}
```

### Example: calendar schedule display

```tsx
{jobs.map((job) => {
  const schedDisplay = typeof job.schedule === "string"
    ? job.schedule
    : (job.schedule_display || job.schedule?.display || "—");
  return (
    <div key={job.id}>
      <span>{schedDisplay}</span>
    </div>
  );
})}
```

## Pattern: `data!` Non-Null Assertion in Guarded Components

When a component guards against `null` with `if (!data) return null;`,
TypeScript's control flow analysis does NOT propagate the non-null
assertion into function bodies defined after the guard.

### ❌ Wrong (TS error: `data` possibly null)

```tsx
export default function Page() {
  const [data, setData] = useState<Data | null>(null);

  function helper() {
    return data.field;  // TS error: 'data' is possibly 'null'
  }

  if (!data) return <Loading/>;
  return <div>{helper()}</div>;
}
```

### ✅ Correct (local non-null alias)

```tsx
export default function Page() {
  const [data, setData] = useState<Data | null>(null);

  // Guard must come before any function that uses data
  if (!data) return <Loading/>;

  function helper() {
    const d = data!;
    return d.field;
  }

  return <div>{helper()}</div>;
}
```

Or, reorder functions inside the JSX return:

```tsx
if (!data) return <Loading/>;

const helper = () => data.field;

return <div>{helper()}</div>;
```

## Pattern: Adding a Modal to a Page

### Step 1: Add state and Modal import

```tsx
import Modal from "@/components/Modal";

// Inside component:
const [selected, setSelected] = useState<ItemType | null>(null);
```

### Step 2: Make cards clickable

```tsx
<div className="... cursor-pointer"
  onClick={() => setSelected(item)}
  role="button" tabIndex={0}
  onKeyDown={(e) => e.key === "Enter" && setSelected(item)}
>
```

### Step 3: Add the modal at the bottom of the JSX

```tsx
<Modal
  open={!!selected}
  onClose={() => setSelected(null)}
  title={selected ? `${selected.icon} ${selected.name}` : ""}
>
  {selected && (
    <div className="space-y-4">
      <p>{selected.desc}</p>
      <div className="grid grid-cols-2 gap-4">
        {/* detail rows */}
      </div>
    </div>
  )}
</Modal>
```

### Step 4: For live data, pass the full API response

```tsx
const [data, setData] = useState<DashboardData | null>(null);
// In the modal:
{agentDetail(selected, data).map((d, i) => (
  <div key={i} className="flex justify-between...">
    <span>{d.label}</span>
    <span>{d.value}</span>
  </div>
))}
```

Where `agentDetail()` is a pure function that returns `{label, value}[]`
based on the selected item's type and the current data snapshot.
