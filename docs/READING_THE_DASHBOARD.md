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

- **The boundary stall.** Every time a new chunk is requested, the arm freezes
  for the full round trip (network + model). In the logs this is the tick
  interval that is ~240 ms instead of 33 ms.
- **Staleness.** Step 0 of a chunk executes right after the observation;
  step 15 executes ~700 ms later, still based on that old picture. Late steps
  in a chunk are "older" decisions than early ones.

`inference_seq` in the CSV numbers the chunks; `horizon_idx` says which step
within its chunk each tick executed (0 = first step of a fresh chunk).

---

## 2. The four signal views

One panel per joint, full run on the x-axis. Click any panel to enlarge it.

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

One row per step-within-chunk (0 … N−1), median over every chunk in the run:

- **err mrad** — tracking error at that step, offset-corrected (each joint's
  constant sag removed so the trend is visible).
- **cmd step** — how big a stride the command takes at that step (max over
  arm joints).

How to read it:

- **Error creeping up** along the rows = late-chunk commands degrade. Gentle
  creep is normal; a cliff means the execution horizon is too long.
- **Row 0's `cmd step` is the splice** — the jump from the previous chunk's
  last command to this chunk's first. This is where chunk-to-chunk
  disagreement (the thing that causes boundary jitter) shows up.
- Comparing two runs with different execution horizons (16 vs 25) in this
  table is the direct way to decide whether a longer horizon is safe.

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

This reconstructs the task storyline from the log alone: when the object was
picked, how long it was carried, when both hands held it (a handoff), when it
was released — or that a grasp closed on air. No video needed.

---

## 8. Run chips (top of the page)

Per selected run: duration, number of chunks, and the request **latency** —
`latency_ms` is the full round trip the robot measured around each chunk
request (packing + network + model + return). p50 is the typical wait, p90
and max show the tail. The very first request of a run is usually slower
(server warm-up).

---

## 9. Comparing two runs

Pick a second run under **Compare with**. Its traces overlay dashed (purple;
in position view its commanded line is amber), its chip appears, and the
tracking + chunk-profile tables grow side-by-side columns. Boundaries and
grasp shading always belong to run A (the sidebar selection).

Typical uses: same episode before/after a checkpoint change; horizon 16 vs
horizon 25; a good run vs the run that failed.
