missions := ("JNO" + "STA")

preview: export
  nbdev_preview

publish: export
  nbdev_proc_nbs && cd _proc && quarto publish gh-pages --no-prompt

quarto-install:
  cd notebooks && quarto add Beforerr/quarto-ext --no-prompt

publish-qrcode:
  segno "https://beforerr.github.io/ids_finder" -o=images/qrcode.png --light transparent --scale 10

export:
  nbdev_export --path notebooks/__init__.ipynb
  nbdev_export

env-create:
  micromamba env create --file environment.yml

env-update:
  micromamba install --file environment.yml

kedro-run-mag-primary mission:
  kedro run --to-outputs={{mission}}.MAG.primary_data_ts_1s

kedro-run-mag-feature mission:
  kedro run --to-outputs={{mission}}.MAG.feature_ts_1s_tau_60s --from-inputs={{mission}}.MAG.primary_data_ts_1s

  kedro run --to-outputs=Wind.MAG.feature_ts_0.09s_tau_60s --from-inputs=Wind.MAG.primary_data_ts_0.09s
  kedro run --to-outputs=events.l1.Wind_ts_0.5s_tau_60s --from-inputs=Wind.MAG.inter_data_h4-rtn
  kedro run --to-outputs=events.l1.Wind_ts_0.2s_tau_60s --from-inputs=Wind.MAG.inter_data_h4-rtn
  kedro run --to-outputs=events.l1.Wind_ts_0.1s_tau_60s --from-inputs=Wind.MAG.inter_data_h4-rtn


kedro-run-mag-feature-all: (kedro-run-mag-feature "JNO") (kedro-run-mag-feature "STA") (kedro-run-mag-feature "THB") (kedro-run-mag-feature "Wind")

kedro-run-candidates mission:
  kedro run --to-outputs=events.{{mission}}_ts_1s_tau_60s --from-inputs={{mission}}.MAG.feature_ts_1s_tau_60s

kedro-run-primary_states:
  kedro run --to-outputs=sta.primary_state_1h 
  kedro run --to-outputs=jno.primary_state_1h
  kedro run --to-outputs=thb.primary_state_1h

kedro-run-sw-events:
  kedro run --to-outputs=events.l1.ALL_sw_ts_1s_tau_60s --from-inputs=JNO.MAG.feature_ts_1s_tau_60s,STA.MAG.feature_ts_1s_tau_60s,THB.MAG.feature_ts_1s_tau_60s,Wind.MAG.feature_ts_1s_tau_60s
  kedro run --to-outputs=events.l1.ALL_sw_ts_1s_tau_60s --from-inputs=events.JNO_ts_1s_tau_60s,events.Wind_ts_1s_tau_60s,events.THB_sw_ts_1s_tau_60s,events.STA_ts_1s_tau_60s
  kedro run --to-outputs=events.l1.Wind_ts_0.5s_tau_60s --from-inputs=Wind.MAG.feature_ts_0.09s_tau_60s

create-mission-notebooks mission:
  mkdir -p notebooks/missions/{{mission}}
  kedro pipeline create {{mission}}
  touch notebooks/missions/{{mission}}/index.ipynb
  touch notebooks/missions/{{mission}}/mag.ipynb
  touch notebooks/missions/{{mission}}/state.ipynb