# Camera playback update / 相机播放更新

This revision keeps the previous v4 webpage layout, numerical evidence, all figures, controls and result links. Only the camera display in the 38 individual MP4/GIF replays, their posters/keyframes, the 10 montages and contact sheets is revised. The CSS is unchanged.

本版保持上一版网页的布局、数值、图表、交互和结果入口。只更新 38 个单场 MP4/GIF 中的相机面板、对应海报/关键帧、10 个合辑及 contact sheet。原版目录完整保留。

The three views are CAM_L1, CAM_F0 and CAM_R1 from the real original nuPlan driving log. There are 21 scene tokens, 63 view sequences and 558 copied real images. Original SQLite exposure timestamps align the images to the scene lidar anchor and the saved BEV physical clock. Local real images are available at approximately 2 Hz, while the saved BEV has its original 0.1 s physical states. Each view holds the latest real exposure at or before the displayed physical time; no generated images, frame interpolation or extrapolated camera motion are used. All slow-playback frame repeats and contact holds retain the previous video timing.

三路相机使用原始驾驶记录的真实照片。按原始曝光时间与 lidar 场景起点对齐，再与 BEV 物理时钟同步。真实图像约 2 Hz，BEV 仍为原始 0.1 秒状态；两张真实图像之间保留上一张。最大图像年龄为 0.49802 秒。慢放与首碰停顿沿用原版，因此视频播放秒数并不等于物理秒数。

**Recorded scene, not model viewpoint.** The camera sequence shows the original logged vehicle, not images generated from each model's simulated ego pose. The camera source is clearly labelled in every frame. The original metadata-associated t0 images remain in `cameras/`. A camera exposure slightly after lidar t0 is not displayed early: the latest prior real exposure is used at t0 instead, and its actual relative capture time is shown.

**相机是原始记录车辆的视角，不是模型模拟车辆视角。** 每帧明确标注来源，并显示实际拍摄时间。原来的 t0 关联图像仍保留；若其曝光晚于 lidar t0，则 t0 播放使用之前的真实曝光，不提前展示之后的信息。

No VLA inference, NAVSIM execution, new experiment, download, GPU work or source-input edits occurred. Model-specific ego/actor states, maps, contact counts, risk features and interpretation boundaries stay unchanged, including ORION AS-RETURNED DIAGNOSTIC / UNRESOLVED.

Alignment evidence: `data/camera_playback_manifest.json`, `camera_playback/physical_time_alignment.csv`, `camera_playback/source_registry.json` and `validation/camera_playback_validation.json`. Source code is saved in `source/camera_playback_v1/`; it was executed from the workspace `work/camera_playback_v1/` with the existing CPU environment. The earlier research reports retain their original contents and numerical evidence; this addendum supersedes only their static-camera description.

Open `index.html` directly in Edge or Chrome; no server or CDN is needed. `videos.html` is the offline media backup.
