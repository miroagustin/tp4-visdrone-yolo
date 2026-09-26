import csv
import json
from pathlib import Path

import pytest

from tp4.bench_common import (PROTOCOL, check_platform, dataset_yaml, inside,
                              percentile, sha, verify_bundle, write_json)
from tp4.benchmark import verify_exports
from tp4.bench_report import compare


def tiny_bundle(root):
    images=[]
    for i in range(300):
        image=f'images/test/{i}.jpg';label=f'labels/test/{i}.txt'
        for rel in (image,label):
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('test')
        images.append(dict(image=image,label=label))
    (root/'models').mkdir();(root/'models/yolo26n.pt').write_bytes(b'checkpoint')
    write_json(root/'reference.json',{})
    m=dict(schema=1,study='yolo26_deployment_v1',split='test-dev',models={'yolo26n':{}},images=images,
           classes=['example'],protocol=dict(PROTOCOL),files={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()})
    write_json(root/'manifest.json',m)
    return m


def test_bundle_hash_missing_and_duplicates(tmp_path):
    m=tiny_bundle(tmp_path)
    verify_bundle(tmp_path)
    label=tmp_path/m['images'][0]['label'];original=label.read_bytes();label.write_bytes(b'changed')
    with pytest.raises(ValueError,match='alterado'):verify_bundle(tmp_path)
    label.write_bytes(original);label.unlink()
    with pytest.raises(ValueError,match='ausente'):verify_bundle(tmp_path)
    label.write_bytes(original)
    m['images'][1]=m['images'][0];write_json(tmp_path/'manifest.json',m)
    with pytest.raises(ValueError,match='duplicad'):verify_bundle(tmp_path)


def test_bundle_resolution_must_match_code(tmp_path):
    m=tiny_bundle(tmp_path)
    m['protocol']['imgsz']=640;write_json(tmp_path/'manifest.json',m)
    with pytest.raises(ValueError,match='regenerar'):verify_bundle(tmp_path)


def test_paths_and_yaml_relocation(tmp_path):
    import yaml
    with pytest.raises(ValueError):inside(tmp_path,'../escape')
    m=tiny_bundle(tmp_path)
    dest=tmp_path/'runtime';dest.mkdir()
    path=dataset_yaml(tmp_path,dest,m)
    assert yaml.safe_load(path.read_text())['path']==str(tmp_path.resolve())
    assert yaml.safe_load(path.read_text())['test']=='images/test'


def test_percentiles():
    assert percentile([40,10,30,20],.5)==25
    assert percentile([40,10,30,20],.95)==pytest.approx(38.5)
    with pytest.raises(ValueError):percentile([],.5)


def test_no_platform_fallback(monkeypatch):
    info=dict(bits=64,architecture='aarch64',board='Jetson',l4t='test',packages={'ultralytics':'8.4.162'})
    monkeypatch.setattr('tp4.bench_common.command',lambda _:None)
    with pytest.raises(RuntimeError,match='CUDA'):check_platform('jetson',info)
    with pytest.raises(RuntimeError,match='Raspberry'):check_platform('rpi5',info)


def test_export_requires_right_format(tmp_path):
    p=tmp_path/'yolo26n.pt';p.write_bytes(b'test')
    record=dict(platform='jetson',bundle_sha='abc',models={n:dict(path=p.name,files={p.name:sha(p)}) for n in ('pytorch','optimized')})
    write_json(tmp_path/'exports.json',record)
    with pytest.raises(ValueError,match='TensorRT'):verify_exports(tmp_path,'jetson','abc')


def test_report_excludes_quick_and_failed(tmp_path):
    source=tmp_path/'quick';source.mkdir()
    write_json(source/'result.json',dict(official=False,status='finished'))
    page=compare([source],tmp_path/'reports')
    text=page.read_text(encoding='utf-8')
    assert 'Sin resultados oficiales' in text and 'excluida' in text
    assert 'http://' not in text and 'https://' not in text


def synthetic_result(root, bundle_sha):
    """Fixture sintética: no se publica como resultado experimental."""
    result=dict(official=True,status='finished',platform='rpi5',bundle_sha=bundle_sha,
                protocol=PROTOCOL,models={},reference={'models':{'yolo26n':{'map50_95':.2}}},
                environment={'synthetic_test_fixture':True},conditions={},exports={'models':{}},gallery=[],caveat='SYNTHETIC TEST')
    for name,fps in [('pytorch',5),('optimized',10)]:
        reps=[]
        for n in range(1,4):
            folder=root/name/f'repeat_{n}';folder.mkdir(parents=True)
            (folder/'timings.csv').write_text('latency_ms\n100\n200\n')
            (folder/'telemetry.csv').write_text('seconds,rss_bytes,temperature_c\n0,1048576,40\n')
            reps.append(dict(fps=fps,images=300*fps,elapsed_seconds=300,rss_peak_bytes=1048576,
                             windows=[dict(start_seconds=0,fps=fps)],effective={},sensors_initial={},sensors_final={},
                             throttle_before=None,throttle_after=None))
        result['models'][name]=dict(repetitions=reps,accuracy={'precision':.4,'recall':.3,'map50':.3,'map50_95':.2})
        result['exports']['models'][name]={'files':{}}
    write_json(root/'result.json',result)


def test_report_groups_and_speedup(tmp_path):
    first=tmp_path/'a';second=tmp_path/'b'
    synthetic_result(first,'hash-a');synthetic_result(second,'hash-b')
    page=compare([first,second],tmp_path/'report')
    text=page.read_text(encoding='utf-8')
    assert 'comparación parcial' in text and 'Se separaron' in text
    assert 'data:image/png;base64,' in text
    with (page.parent/'comparacion.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==4
    assert float(rows[1]['speedup_vs_pt'])==2
    assert float(rows[1]['delta_vs_pt_device_pp'])==0
