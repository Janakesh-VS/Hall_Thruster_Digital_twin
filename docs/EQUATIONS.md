# PROMETHEUS — Phase 4 Physics: Equation Documentation

Reduced-order (0-D, single operating point), not a kinetic/PIC plasma
simulation. Every equation below is implemented in
`src/physics/hall_thruster.py` and is cited to a primary/authoritative
source — nothing here is an invented relationship.

---

## 1. Ion exhaust velocity

```
v_i = sqrt( 2 * e * (V_d - Delta) / m_i )
```

| Variable | Meaning | Unit |
|---|---|---|
| v_i | mean ion exhaust velocity | m/s |
| e | elementary charge | C |
| V_d | discharge voltage | V |
| Delta | voltage losses | V |
| m_i | ion mass (propellant atomic mass / charge state) | kg |

**Assumptions:** ions singly charged; all ions created at one location and
fall through the same potential drop; Delta = 0 by default (voltage losses
neglected, per source's baseline case).

**Source:** Boeuf, J.-P. & Garrigues, L., *"Sizing of Hall Effect Thrusters
with Input Power and Thrust Level: An Empirical Approach,"* arXiv:0810.3994,
Eq. (2.17).

**Limitations:** ignores electron temperature, multiply-charged ions, beam
divergence. Order-of-magnitude / scaling estimate, not high-fidelity.

---

## 2. Ion kinetic energy

```
E_i [eV] = V_d - Delta
E_i [J]  = e * (V_d - Delta)
```

Direct consequence of Eq. 1's assumption. Status: **MODELLED**.

---

## 3. Discharge power

```
P_d = V_d * I_d
```

Standard definition, consistent with the Hall-thruster power balance
`P_dis = V_D * I_D` used throughout the electric-propulsion literature.
Status: **MODELLED**.

---

## 4. Ion flux (particle rate)

```
N_dot_ion = (eta_m * m_dot) / m_i
```

| Variable | Meaning | Unit |
|---|---|---|
| eta_m | mass utilization efficiency (**ASSUMED**, see `config/operating_conditions.yaml`) | fraction |
| m_dot | propellant mass flow rate | kg/s |

Status: **ESTIMATED** — depends on an assumed efficiency factor, not a
measured quantity.

---

## 5. Thrust

```
T_ideal    = m_dot * v_i                    (IDEAL — no losses)
T_estimate = eta_m * m_dot * v_i            (ESTIMATED)
```

**Source:** standard electric-propulsion thrust relation (thrust = mass
flow rate x exhaust velocity), consistent with the treatment in Boeuf &
Garrigues (2009) and Dannenmayer, K. & Mazouffre, S., *"Elementary Scaling
Relations for Hall Effect Thrusters,"* EUCASS Proceedings / J. Propulsion
and Power framework (2011/2012), https://doi.org/10.1051/eucass/201102601.

Status: `thrust_ideal_N` = **IDEAL** (upper bound). `thrust_estimate_N` =
**ESTIMATED**. Neither is an experimentally measured thrust.

---

## 6. Specific impulse

```
Isp = T_estimate / (m_dot * g0)
```

`g0 = 9.80665 m/s^2` (ISO 80000-3, defined standard value).
Status: **ESTIMATED**.

---

## Sanity check against published data

At the reference operating point (300 V, xenon, mass utilization 0.7,
voltage loss = 0), the model gives Isp ≈ 1499 s. Published 300 V-class
xenon Hall thrusters (e.g. University of Michigan PEPL magnetically
shielded thruster characterizations) report Isp in the 1500-2300 s range
at similar or higher discharge currents — our reduced-order estimate is
in the right order of magnitude and on the low end, which is expected
given the neglected voltage losses assumption interacts with a
conservative mass-utilization efficiency choice (0.7). This is a plausibility
check only, **not a validation** — PROMETHEUS is a different, hypothetical
thruster with no measured performance data of its own.

## What this model does NOT do

- No spatial resolution of the discharge channel (0-D only).
- No electron temperature, multiply-charged ion, or beam-divergence
  correction.
- Magnetic field is a **model input**, not computed (Phase 5 will replace
  the scalar placeholder in `src/magnetic/interface.py` with a real
  reduced-order or FEMM-derived field model).
- No erosion, wall-exposure, or controller logic yet (Phases 6-10).

## Full reference list

See `references/references.bib` for BibTeX entries, including the two
added in this phase (Boeuf & Garrigues 2009; Dannenmayer & Mazouffre 2011)
alongside the five references from the SIH presentation itself.
