# Reading the dashboard

Plain-English guide to every plot and table on the page, and the ideas behind
them. Read the first section even if you skip the rest — everything else uses
the word *chunk*.

---

## 1. What a chunk is

The robot does not ask the model "what do I do now?" thirty times a second.
Inference is far too slow for that. Instead:

1. The robot takes one observation — three camera images + all joint positions.
2. It sends that to the model and **waits** (the arm holds still).
3. The model returns a **chunk**: a list of future steps (e.g. 40 of them),
   each one a full set of joint positions for one control tick.
4. The robot plays the first N steps of that chunk at 30 Hz (N is the
   *execution horizon*, e.g. 16 → ~533 ms of motion), **blind** — it does not
   look at the world again while playing.
5. The buffer runs out → back to step 1.

Two consequences show up all over the dashboard:

- **The boundary stall (blocking runs).** In the original loop, every new
  chunk request froze the arm for the full round trip (network + model) — in
  the logs, a tick interval of ~240 ms instead of 33 ms.
- **Staleness.** Step 0 of a chunk executes right after the observation;
  step 15 executes ~700 ms later, still based on that old picture. Late steps
  in a chunk are "older" decisions than early ones.

`inference_seq` in the CSV numbers the chunks; `horizon_idx` says which step
of its chunk each tick executed.

### Prefetch and RTC runs (client v0.4+)

Two per-run options change the picture, and logs of all kinds can sit in the
same folder:

- **Prefetch** — the next chunk is requested on a background thread while the
  current one is still playing, so the arm never stops. Because the round
  trip (~270 ms ≈ 8–9 steps) elapses while the arm keeps moving, the steps
  that went stale in flight are **skipped** on arrival: a chunk's first
  executed `horizon_idx` is typically 7–12, not 0. Chunks are also
  **truncated** — a fresh chunk replaces whatever was left of the old buffer
  — so executed steps-per-chunk varies.
- **RTC** — each request carries the previous chunk back, and the server
  grows the new chunk out of it instead of from scratch, to smooth the seam
  between chunks.

The dashboard detects boundaries from `inference_seq` changes (never from
`horizon_idx == 0`), so all of it works for both kinds of run. In a prefetch
run a long tick gap is no longer expected — it means the buffer ran dry
(**starvation**), which is a bug, and it shows up under *stalls* in Run facts.

Runs from client v0.4+ also ship a `<run>.meta.json` **sidecar** with the full
configuration (checkpoint label, prefetch/RTC settings, execution horizon…).
It feeds the config line under Run facts and the run-matrix columns. Older
runs show "config unknown" — everything else still works.

---

## 2. The five signal views

One panel per joint, full run on the x-axis. Click a panel's **title** to
enlarge it; the plot area itself is for zooming (next section). The section
heading always names what is currently plotted and its units, so it reads
"Measured joint effort (Nm)" rather than a generic label.

**Hiding runs.** Each run in the sidebar has a **×** that removes it from the
compare list, the run matrix and the scatter plots — useful when a folder holds
smoke tests or aborted attempts you do not want skewing a comparison. The row
stays greyed with a **+** to restore it (clicking the name works too), the
choice persists between visits, and the last visible run cannot be hidden.

### Zooming — the plots hold every sample

The page embeds the raw command and actual-position arrays, so zooming reveals
real data, not bigger pixels:

- **scroll** on any plot zooms around the cursor; **drag** pans;
  **double-click** resets to the full run.
- The time window is **shared across every panel** (and the enlarged view), so
  all joints stay aligned while you move around.
- Detail appears as you go: far out you see today's overview line; closer, the
  chunk boundaries get labelled with their chunk number and the **splice size
  in mrad**; closest, every sample becomes a dot with its `horizon_idx`
  underneath — a chunk starting at 9 instead of 0 makes the prefetch skip
  directly visible.
- The x-axis is real time (`t_rel`), so a blocking run's boundary stall shows
  as a genuine gap between dots, while a prefetch run stays evenly spaced.
  That contrast is itself diagnostic.
- **Click any table row that carries a time or chunk number** — a contact, a
  grasp attempt, the worst splice in Run facts — and the plots jump to that
  moment.
- **Hover anywhere on any plot to read its values.** A crosshair marks the
  instant and a tooltip gives the numbers: on a joint panel, the time, each
  line's value with units, and which chunk and step that instant belongs to
  (both runs at once in compare mode). The chunk-profile, step-distribution
  and matrix scatter plots report their own values the same way.

Velocity and effort are stored decimated (they are read as envelopes), so
their zoom bottoms out earlier. A very long run past the size budget falls
back to decimated-only entirely; its chip says "raw omitted".

### position
Two raw lines straight from the CSV: **actual** (blue, the encoder) and
**commanded** (red, what the model asked for). Good for seeing the *shape* of
the motion and gross weirdness.

> ⚠ Each panel autoscales its own y-axis. A joint sweeping 2 radians makes a
> 100 mrad error look like nothing; a joint that barely moves makes a tiny
> error look dramatic. **Never judge error size from this view** — that is
> what the error view and the tracking table are for.

### error
Commanded minus actual, in **mrad** (1 mrad ≈ 0.057°), around a zero line.
Distance from zero is the real tracking error, no scale tricks. Faint red
verticals (toggle: *chunk boundaries*) mark where each new chunk began.

A line that sits at a constant offset from zero is **sag** (see §4). A line
that spikes during motion and returns to zero is **lag**.

### cmd step
**What the splice ratio is made of.** One full-width panel: `|Δcmd|` per tick
in mrad — how far the command moved this tick — max over the arm joints
(fingers excluded, matching how the splice ratio pools it). Inside a chunk it
is a low band; at a chunk switch it spikes. The dashed green line is the
within-chunk median, so the splice ratio is literally the height of the
spikes over that line. Zoom into any spike to see the exact boundary.

### velocity / effort
The raw measured streams. Both look noisy — that is the sensor, not the arm:
velocity is computed by differentiating encoder positions (which amplifies
every encoder tick), and effort is estimated from motor current (which
carries controller ripple, cogging and friction). Read the **envelope**, not
the fuzz: in effort, the slow rise and fall over seconds is gravity load
changing with pose; in velocity, sustained departures from zero are real
motion.

---

## 3. Tracking table

One row per joint, all values in mrad:

| column | meaning |
|---|---|
| **p50** | typical gap between commanded and actual (median over the run) |
| **p95** | the gap in the worst 5% of moments |
| **lag ms** | time shift that best aligns command with actual — how far behind the arm runs. "—" = the joint never moved enough to tell |
| **mid** | error during mid-chunk, while actively following commands |
| **bnd** | error on the first tick after the boundary stall, when the arm had ~240 ms to catch up to a frozen command |

**mid vs bnd is a built-in diagnosis.** If `bnd` is much smaller than `mid`,
the joint *lags* — give it time and it catches up. If they are equal, the
joint holds a **standing offset** — extra time doesn't help. On the adibot,
they are equal: the arm sags under gravity (see §4).

`bnd` only exists for **blocking-style runs** (the dashboard checks whether
boundaries actually carried a stall). In a prefetch run there is no catch-up
time at a boundary, the diagnosis is undefined, and the column shows "—".

Large p50 values are highlighted (threshold in `config.py`).

---

## 4. About the sag (why big errors can be normal)

On this arm, several joints track their commands with a large constant offset
(up to ~220 mrad ≈ 13° on the gravity-loaded lift joints). This is
**compliance sag**: the position controller holds like a spring, and gravity
torque pulls the joint off its setpoint proportionally (error ≈ torque ÷
stiffness). It is not a bug in the logs or the policy — and crucially, the
same sag existed while the training demonstrations were recorded, so the
policy learned to command "high" and the task still works.

Practical rule: on this arm, `cmd − actual` is **offset + small dynamics**,
not a clean error signal. The dashboard handles this two ways:

- the chunk profile subtracts each joint's own run-median offset before
  looking at trends, and
- nothing anywhere uses a gravity *model* — every baseline is measured from
  the run itself, so the numbers stay correct on a robot with different
  (or no) sag.

---

## 5. Chunk profile

Answers: **do commands get worse the further you are into a chunk?**
(They execute on an older observation, so they might.)

Shown as a **plot first** — error (solid) and command step (dashed) against
`horizon_idx`, compare run overlaid in purple — because the thing being looked
for is a **knee**: the step where late commands stop being trustworthy. The
table below it carries the exact numbers. One row per **observed**
`horizon_idx`, median over every chunk in the run.
For a blocking run the rows run 0 … N−1; for a prefetch run they start where
the skip lands (typically 7–12) and reach as deep as execution ever got.

- **err mrad** — tracking error at that step, offset-corrected (each joint's
  constant sag removed so the trend is visible).
- **cmd step** — how big a stride the command takes at that step (max over
  arm joints). Chunk-switch ticks are excluded — the jump across a switch is
  the *splice* and is reported separately under Run facts.

How to read it:

- **Error creeping up** along the rows = late-chunk commands degrade. Gentle
  creep is normal; a cliff means execution is reaching too deep.
- The **deepest rows** are the ones grasp attempts care about: an attempt
  issued deeper than the usable depth tends to fail (see Run facts / matrix,
  `depth p95`).
- Comparing two runs with different execution horizons (16 vs 25) in this
  table is the direct way to decide whether a longer horizon is safe.

---

## 5b. Run facts

The per-run summary next to the tracking table. All "—" on a metric means the
log doesn't carry what it needs (old format), never an error.

**Scheduling** — *replan cycle* (executed steps between chunk switches; with
truncation this is a distribution, not a constant), *skip on arrival*
(measured `min horizon_idx` per chunk, cross-checked against the logged
`skip_steps`), *executed depth* (max `horizon_idx` per chunk — how deep into
its prediction the run actually played; p95 is the number to watch),
*stalls* (tick gaps > 100 ms: expected in a blocking run, **starvation** in a
prefetch run), *starved ticks* (`buffer_len` hit 0), *effective rate*, and
*RTC applied* (fraction of chunks that really carried a previous chunk — the
first one never does).

**Smoothness** (arm joints only; grippers step sharply by design) —
*cmd step within / at splice* and their ratio: the **splice ratio**, the
headline smoothness number. 1× means a chunk switch moves the command no more
than an ordinary tick; the historical bad value on this arm was 16×. Also
splice p95/max with the offending chunk number, command jerk in both pools,
reversing-joint counts at splice vs within (only the excess over the within
baseline matters), and the velocity spike within ±3 ticks of a splice.

One honest caveat: in a *blocking* run the splice interval spans the ~240 ms
stall, so its command jump is naturally larger than a 33 ms step — compare
splice ratios between runs of the same kind, and check `stalls` to know which
kind a run is.

**Step distribution** — the histogram under the facts table. It answers one
question: *how big are the arm's command steps, and are the ones at chunk
switches really different?*

Every control tick moves the command some distance (`|Δcmd|`, max over the arm
joints — the same series the *cmd step* view plots). Sort those ticks into two
piles: the ones **inside a chunk** (teal) and the ones **at a chunk switch**
(amber). The x-axis is step size in mrad, up to the 99th percentile; the height
of each curve is how many ticks fell in that size bin, each curve scaled to its
own peak so the small amber pile stays visible next to the large teal one.

How to read it:

- **Teal alone, tight and low** — ordinary motion; that hump's position is the
  arm's normal per-tick step.
- **Amber sitting on top of teal** — chunk switches move the command no more
  than an ordinary tick. This is what smooth looks like.
- **Amber shifted right of teal** — every switch jumps further than a normal
  step: a consistent splice, exactly what the splice ratio reports.
- **Amber mostly overlapping but with a long thin tail** — most switches are
  fine and a few are terrible. The median-based splice ratio would look
  moderate while the arm still jerks occasionally; this is the case the ratio
  alone cannot show you.

Hover any bin to see the exact size range and how many ticks of each kind fell
in it.

**Safety** — the fraction of ticks where the limit guard held a side instead
of publishing. A high rate invalidates the run's smoothness numbers: held
ticks repeat the old command, which fakes smoothness.

---

## 6. Contacts table

Moments the arm pushed against something, or something pushed back.

Each joint's effort is mostly gravity, which changes slowly with pose. The
detector subtracts a ~1 s rolling median of the joint's *own* effort (a
self-measured baseline — no robot model) and flags sudden leftovers: table
hits, grasps taking load, bumps, snags.

| column | meaning |
|---|---|
| t (s) | when, on the same clock as the plots |
| dur ms | how long the force lasted |
| joint | which joint felt it most |
| peak Nm | how hard (large values highlighted) |

Caveats:

- A very sharp *intentional* acceleration also spikes effort. Treat rows as
  "look here", not verdicts — click into the effort plot at that time.
- The rolling baseline absorbs sustained forces within ~1 s, so the table
  finds when a contact **began**, not how long a lean lasted.
- Expected events (grasps, handoffs) line up with the grasps table; the
  interesting rows are the ones that don't line up with anything planned.

---

## 7. Grasps

For each gripper finger: the time spans where the finger was **commanded
closed but stopped short** — meaning an object was physically blocking it.
Shown as green shading on the finger panels and as time ranges in the table.

**The shading only appears for a finger that demonstrably follows its
command.** A disabled or unpowered gripper ignores commands entirely, so the
gap between commanded and actual is permanent — shading that would claim the
hand held something for the whole run. Likewise a finger whose command never
moves (a parked side) has no meaningful range to measure a gap against. In
both cases the panel is left unshaded and the Grasps list says *not measured*
with the reason, so an empty result is never mistaken for "it never grabbed
anything". Close attempts on such a finger still appear, with *outcome not
measurable* instead of held/air.

This reconstructs the task storyline from the log alone: when the object was
picked, how long it was carried, when both hands held it (a handoff), when it
was released — or that a grasp closed on air. No video needed.

Below the spans, every **close attempt** is listed with:

- the **step** (`horizon_idx`) it was issued at — attempts issued deeper than
  the usable depth tend to fail, and this measures that directly across runs;
- the **rise time** of the close command (10→90% of the drop) — RTC's
  blending stretches commands, so a lengthening rise time is the test for
  "RTC is smearing the grasp";
- for RTC runs, whether the close landed **inside the RTC overlap region**
  (the early steps the server blends with the previous chunk);
- **✓ held / ✗ air** — whether the finger actually stopped on something.

---

## 8. Run chips (top of the page)

Per selected run: duration, number of chunks, the run kind
(blocking / prefetch / prefetch+RTC — from the sidecar, or guessed from
whether boundaries stall when there is none), request **latency** p50
(`latency_ms` is the full round trip the robot measured around each chunk
request), executed **depth p95**, the **splice ratio**, and the **stall
count**. The very first request of a run is usually slower (server warm-up).

---

## 9. Comparing two runs

Pick a second run under **Compare with**. Its traces overlay dashed (purple;
in position view its commanded line is amber), its chip appears, and the
tracking + chunk-profile tables grow side-by-side columns. Boundaries and
grasp shading always belong to run A (the sidebar selection).

Typical uses: same episode before/after a checkpoint change; horizon 16 vs
horizon 25; blocking vs prefetch on the same task; a good run vs the run
that failed.

---

## 10. Run matrix

The page for deciding **which configuration wins**. One row per run:
configuration from the sidecar (checkpoint, mode, execution horizon) beside
the measured behaviour (cycle, skip, depth p95, splice ratio, stalls,
effective Hz, grasp successes/attempts, latency, limit-guard rate).

**Verdict chips** mark whether a run is a valid comparison point at all:
stalls = 0, splice ratio below the configured limit, depth p95 inside the
usable range, no limit-guard holds. A run failing a chip isn't "worse" — its
*other* numbers just can't be trusted for comparison, because the failure
contaminates them.

Two plots at the bottom: **splice ratio vs replan cycle** (does replanning
more often cost smoothness?) and **grasp success vs executed depth p95** —
if grasps fail past a depth, the cliff appears here. Threshold lines come
from `config.py` and are checkpoint-specific: re-measure before trusting
them on a new model.

---

## 11. Full-chunk metrics (runs with a `.chunks.npz`)

Clients with `log_chunks` (post-v0.5) write a third file per run holding every
action chunk **in full** — including the ~24 of 40 steps that are never
executed. Three measurements become possible, shown in Run facts and on the
chunk-profile plot; runs without the file show "—".

- **Chunk overlap disagreement** — consecutive chunks describe the *same
  instants* (each chunk is anchored in time through the CSV), so their
  difference over the whole shared stretch is the true chunk-to-chunk
  stability number. The executed-only *splice ratio* sees one step of this;
  the overlap disagreement sees all ~24. Reported as p50/p95 over all chunk
  pairs plus the worst pair — click it to jump there.
- **RTC frozen-region mismatch** — with RTC on, the first `rtc_frozen_steps`
  of each new chunk should *equal* the previous chunk at those instants.
  This reports the actual mismatch in mrad; near zero means the server
  honoured the freeze, anything larger means RTC is not doing what its
  parameters claim.
- **Discarded-tail error** — each chunk's unexecuted steps compared against
  what was *actually commanded* at those instants by later chunks, drawn as
  the dotted amber line on the chunk-profile plot (by `horizon_idx`, hover
  for values). Flat and low = the deep tail was still a good prediction, and
  executing deeper (a larger execution horizon) is safe; rising steeply =
  the tail is stale guesswork and deeper execution would act on it.

### The plans page

The third page draws the predictions themselves, and is where the schedule
becomes visible rather than numeric.

**Every plan, per joint** — one panel per joint. Each faint line is one whole
chunk, drawn on the time axis from the instant it was planned for, so
consecutive chunks physically overlap where they describe the same moments.
Where two lines separate, that gap *is* the disagreement. The solid red line
is what the arm was actually commanded.

Each plan is coloured by region:

| colour | region | meaning |
|---|---|---|
| light blue | RTC frozen | the server was told to keep these identical to the previous chunk |
| teal-green | RTC ramp | the blend region between frozen and free |
| grey | skipped | expired in flight, discarded on arrival |
| solid teal | executed | actually drove the arm |
| grey dashed | discarded tail | predicted, then replaced by the next chunk |
| **solid red line** | the prefetch cut | everything left of it was skipped |
| red dashed line | superseded | where the next chunk took over |

**One thing to look for immediately:** if the solid red prefetch cut sits to
the *right* of the light-blue frozen band, RTC's frozen steps were all
discarded before they could drive anything — the freeze is configured but
never reaches the arm. That is `rtc_frozen_steps` being smaller than the skip,
and it is invisible in every other view.

Plans are drawn only when the visible window is short (8 s by default,
`plans_window_s`) — a whole run of overlaid chunks is an unreadable smear.
Zoom with the scroll wheel; the hint above the grid says which mode you are in.

**Disagreement between consecutive plans** — the aggregate at the top of the
page. For every chunk pair, how far apart the two plans are about the same
instant, plotted against how many steps past the switch that instant is:
median line with a p10–p90 band, over every pair in the run. The same region
bands sit behind it, so you can see whether disagreement grows inside the
executed region or only out in the discarded tail. Flat and low means each new
plan simply continues the old one.

The run matrix gains an **overlap mrad** column so configurations can be
compared on true stability, not just the one-step splice.
