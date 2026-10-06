# Drive2Survive：四模型研究结果 / Four-model research evidence

## 研究目标 / Research objective

根据上传的研究方案，本项目要回答：VLA 规划在长尾危险场景中是否保有安全间隔，累计近失风险是否能补充单纯碰撞计数，以及在保留进度和舒适性的前提下能否识别并减少后续接触。此页面仅使用现有 Dev100 证据；不能据此声称已覆盖全部长尾分布。

The proposal motivates a reproducible benchmark of VLA driving behavior in long-tail situations. Pre-crash precursor metrics complement contact counts; progress and comfort discourage a trivial stop-to-be-safe solution. Current saved Dev100 evidence supports descriptive comparisons and exploratory threshold analysis, not population-level validation.

## 执行与接触 / Execution and contact

|Model|Common 3 s|Available horizon|Available contacts|Valid n in each view|
|---|---:|---:|---:|---:|
|AutoVLA|2|4 s|12|100|
|Impromptu-VLA|6|3 s|6|100|
|ORION|3|4 s|13|100|
|OpenDriveVLA|2|3 s|2|100|

每模型每视图均成功100、失败0、未运行0。接触是实际采样时刻的 OBB 接触或重叠，按场景计数，不是 native NC。ORION 保留 AS-RETURNED DIAGNOSTIC / UNRESOLVED。4 s 比较不是公平排行榜。

All models retain 100/100 valid scenes, with zero failed or not-run statuses in these saved banks. ORION remains diagnostic. Independent 3 s and 4 s executions have different prefixes for AutoVLA and ORION; a count difference is not the last-second increment.

## 五个指标 / Five metrics

TTC uses the existing frozen-heading, constant-velocity OBB collision search (3 s search horizon). DRAC retains the existing aligned closing-conflict definition. PET retains the saved conflict-zone definition and applicability. The proposal contains simplified motivation formulas; they do not replace the saved operational implementation.

PDF = a density histogram conditional on finite values; all models use common bins determined from feature values only. ECDF is finite-conditional except TTC: its denominator also retains right-censored scenes and only the range below 3 s is identified. N/A, censoring and incomplete values remain distinct. No curve is P(contact | threshold). TET is discrete at 0.1 s, so its density histogram is a binning display, not an assumed continuous law.

TET = Σ Δt·1[0 ≤ TTC < 3 s]; TIT = Σ Δt·max(0,3−TTC). Right endpoint integration, t0 has Δt=0. Unknown TTC remains unknown; known censoring beyond the search window adds no below-threshold exposure.

|Model|Mean TET full (s)|Mean TET pre-contact (s)|Mean TIT full (s²)|TTC finite / censored|
|---|---:|---:|---:|---|
|AutoVLA|0.255|0.248|0.282|24 / 76|
|Impromptu-VLA|0.270|0.228|0.445|19 / 81|
|ORION|0.344|0.305|0.458|26 / 74|
|OpenDriveVLA|0.201|0.195|0.230|18 / 82|

Full and pre-contact statistics are not interchangeable. Full windows include post-contact TTC=0; strict pre-contact windows are outcome-dependent and retrospective. Neither is a uniform early-prediction window.

## 固定时点阈值 / Fixed-landmark threshold selection

先观察 [0,L]，排除首次接触≤L的场景，再预测首次接触在 (L,U] 的目标。PET 在截止时刻无法合法获得时标 N/A。全部目标接触覆盖率包括指标不适用的接触；metric-eligible recall 分母不同。

Reference rule: common 3 s; L=1 s; future interval (1,3]; TIT > 1 s² observed only in [0,1]. AutoVLA 1/2 selected with coverage 1/2; Impromptu 2/4 with coverage 2/6; ORION 3/4 with coverage 3/3; OpenDriveVLA 1/2 with coverage 1/2. No model reaches 80% under this shared rule.

The same-bank original threshold grid may reach the following targets. The largest selected set that meets each target is retained; thresholds were not altered to obtain a preferred result.

|Model|Metric|Target|Threshold|k/n|All-target coverage|Wilson 95%|Status|
|---|---|---:|---|---|---|---|---|
|AutoVLA|TTC|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|TTC|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|TTC|80%|< 0.3|1/1|1/6|20.7–100.0%|LOW_SUPPORT|
|Impromptu-VLA|TTC|90%|< 0.3|1/1|1/6|20.7–100.0%|LOW_SUPPORT|
|ORION|TTC|80%|< 0.3|1/1|1/3|20.7–100.0%|LOW_SUPPORT|
|ORION|TTC|90%|< 0.3|1/1|1/3|20.7–100.0%|LOW_SUPPORT|
|OpenDriveVLA|TTC|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|OpenDriveVLA|TTC|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|TIT|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|TIT|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|TIT|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|TIT|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|ORION|TIT|80%|> 1.76262|1/1|1/3|20.7–100.0%|LOW_SUPPORT|
|ORION|TIT|90%|> 1.76262|1/1|1/3|20.7–100.0%|LOW_SUPPORT|
|OpenDriveVLA|TIT|80%|> 1.33752|1/1|1/2|20.7–100.0%|LOW_SUPPORT|
|OpenDriveVLA|TIT|90%|> 1.33752|1/1|1/2|20.7–100.0%|LOW_SUPPORT|
|AutoVLA|DRAC|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|DRAC|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|DRAC|80%|> 0.846413|4/5|4/6|37.6–96.4%|LOW_SUPPORT|
|Impromptu-VLA|DRAC|90%|> 0.893666|4/4|4/6|51.0–100.0%|LOW_SUPPORT|
|ORION|DRAC|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|ORION|DRAC|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|OpenDriveVLA|DRAC|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|OpenDriveVLA|DRAC|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|PET|80%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|AutoVLA|PET|90%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|Impromptu-VLA|PET|80%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|Impromptu-VLA|PET|90%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|ORION|PET|80%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|ORION|PET|90%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|OpenDriveVLA|PET|80%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|OpenDriveVLA|PET|90%|N/A|N/A|N/A|N/A|NO_ELIGIBLE_DATA|
|AutoVLA|TET|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|AutoVLA|TET|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|TET|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|Impromptu-VLA|TET|90%|N/A|N/A|N/A|N/A|NOT_REACHED|
|ORION|TET|80%|> 0.8|3/3|3/3|43.9–100.0%|LOW_SUPPORT|
|ORION|TET|90%|> 0.8|3/3|3/3|43.9–100.0%|LOW_SUPPORT|
|OpenDriveVLA|TET|80%|N/A|N/A|N/A|N/A|NOT_REACHED|
|OpenDriveVLA|TET|90%|N/A|N/A|N/A|N/A|NOT_REACHED|

所有达到目标的参考窗口候选均只有1–5个选中场景；没有一个候选的 Wilson 95% 下界达到其80%/90%目标。单一1/1、3/3、4/5不能解释为稳定危险概率。Wilson区间也没有校正选阈值偏差与共享日志的相关性。

Selected groups are small and thresholds are explored on the same bank. Wilson intervals are descriptive, not a calibrated prediction guarantee, and do not correct for threshold selection or shared-log dependence.

## 视频 / Videos

38 unique saved contact executions, 38 H.264 MP4, 38 GIF, 38 posters and 38 four-time keyframe sheets. The common-3 s view references 13 model-scene contacts; the available view references 33. Impromptu and OpenDriveVLA reuse identical 3 s executions across views; 8 references are shared. Ten compilations cover both scopes, four models plus all-model compilation in each.

21 unique scene tokens have 63 source-hash-verified real t0 camera images and real nuPlan map geometry. All 38 replays combine three held t0 views with original 0.1 s ego/actor states, physical time, contact actor/type/relative sector, five timelines and contact marker. No interpolation or fabricated future camera frames. Cameras are verified scene observations, not proof of identical model input preprocessing.

## 可总结的规律 / Patterns with limits

1. 时域增加会改变执行与暴露机会；两套结果必须分开。 / Horizon affects both execution and exposure; keep the two views separate.
2. TTC多数为右删失；DRAC和PET适用面不同，因此密度曲线的分母不相同。 / TTC has a large censored tail; DRAC/PET have narrower applicability.
3. TET的时长与TIT的严重程度互补；零风险质量和尾部应一起报告。 / Duration and accumulated severity are complementary; retain zero mass and tails.
4. 高精度往往来自很小选中集；覆盖率和不确定性必须同时看。 / High selected fractions can rely on very small groups; report coverage and uncertainty.
5. 下一步应在独立bank增加接触样本、验证阈值迁移，再结合进度与舒适性测试干预。 / Next steps are held-out threshold validation and intervention evaluation with progress and comfort.

Existing plans were executed using saved official-backend results. This page does not imply fresh VLA replanning, a newly completed larger bank, causal intervention benefits, or certified ORION native coordinates/timing.