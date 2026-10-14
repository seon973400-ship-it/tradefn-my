#!/usr/bin/env python
"""Orange 3.40 워크플로(.ows)를 코드로 만들고, Orange가 여는 방식 그대로 다시 열어 끝까지 실행해 검사하는 공용 함수.

`tools/build_day2_orange.py` · `tools/build_day3_orange.py`가 import한다(단독 실행하지 않는다).

만드는 방식 — Orange 캔버스의 '저장'과 같은 경로
  1. `WidgetsScheme`(캔버스가 쓰는 모델)에 위젯을 놓고 연결한다. basedir(= .ows가 놓일 폴더)에 실제 데이터 사본을 둔다.
  2. 데이터가 위젯을 끝까지 흐르게 한 뒤 역할 · 조건 · Target 같은 '데이터에 묶인 설정(context)'을 위젯 API로 정한다.
  3. `sync_node_properties()` → `scheme_to_ows_stream(pickle_fallback=True)`로 쓴다.
  4. 정리: File 위젯은 basedir 상대 경로(prefix='basedir')만 남기고 만든 PC의 절대 경로를 지운다 · Save Data의 저장 폴더는 '.'
     (= .ows 폴더) · 창 위치(savedWidgetGeometry)는 뺀다 · Qt 객체가 피클에 섞이면 멈춘다(PyQt5/PyQt6 설치판 모두 열리게).

검사
  - `load_check()`: 저장한 .ows를 새 WidgetsScheme로 다시 읽어(scheme_load) 알 수 없는 위젯 0 · 노드 · 링크 수를 확인한다.
  - `run_ows()`: 데이터와 함께 새 폴더에 복사해 열고(basedir = 그 폴더) 신호가 멈출 때까지 실행한 뒤 위젯을 돌려준다.

필요 패키지(수업용 requirements와 별도, 강사 PC 전용):
  pip install "Orange3==3.40.0" PyQt5 Orange3-Explain xgboost
화면 없이 돈다(QT_QPA_PLATFORM=offscreen).
"""
from __future__ import annotations

import copy
import io
import logging
import os
import pickletools
import re
import shutil
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
logging.getLogger("orangewidget").setLevel(logging.ERROR)
logging.getLogger("orangecanvas").setLevel(logging.ERROR)

from AnyQt.QtCore import QCoreApplication, Qt  # noqa: E402
from AnyQt.QtWidgets import QApplication  # noqa: E402

ORANGE_VERSION = "3.40"
NOTE_FONT = {"family": "Malgun Gothic", "size": 12}

_APP = None
_REG = None


def app():
    """오프스크린 QApplication(한 프로세스에 하나)."""
    global _APP
    _APP = QApplication.instance() or QApplication(["orange-ows"])
    return _APP


def versions() -> dict:
    from importlib.metadata import version
    import Orange

    out = {"Orange3": Orange.version.version}
    for dist in ("orange-canvas-core", "orange-widget-base", "Orange3-Explain", "xgboost", "scikit-learn"):
        try:
            out[dist] = version(dist)
        except Exception:  # noqa: BLE001
            out[dist] = None
    return out


def check_versions() -> dict:
    v = versions()
    if not str(v["Orange3"]).startswith(ORANGE_VERSION):
        print(f"[주의] Orange {v['Orange3']} — 수업 기준은 {ORANGE_VERSION}입니다. 만든 .ows는 열리지만 설정 이름이 다를 수 있습니다.")
    if not v.get("Orange3-Explain"):
        raise SystemExit("Orange3-Explain 애드온이 없습니다: pip install Orange3-Explain")
    if not v.get("xgboost"):
        raise SystemExit("xgboost가 없습니다(Gradient Boosting의 xgboost 방식): pip install xgboost")
    return v


def registry():
    """Orange + 애드온 위젯 목록(캔버스와 같은 발견 절차)."""
    global _REG
    if _REG is None:
        app()
        from orangecanvas.registry import WidgetRegistry
        from orangewidget.workflow.discovery import WidgetDiscovery
        from Orange.canvas import config

        reg = WidgetRegistry()
        WidgetDiscovery(reg).run(config.widgets_entry_points())
        _REG = reg
    return _REG


def widget_class(qualified_name: str):
    import importlib

    mod, _, cls = qualified_name.rpartition(".")
    return getattr(importlib.import_module(mod), cls)


def process(seconds: float = 0.0):
    end = time.time() + seconds
    while True:
        QCoreApplication.processEvents()
        if time.time() >= end:
            break
        time.sleep(0.01)


class Flow:
    """캔버스 하나. key로 노드를 부른다."""

    def __init__(self, title: str, description: str, basedir: Path):
        app()
        from orangecanvas.scheme.widgetmanager import WidgetManager
        from orangewidget.workflow.widgetsscheme import WidgetsScheme

        self.basedir = Path(basedir)
        self.scheme = WidgetsScheme(title=title, description=description)
        self.scheme.set_runtime_env("basedir", str(self.basedir))
        self.scheme.widget_manager.set_creation_policy(WidgetManager.Immediate)
        self.nodes: dict = {}

    # ----------------------------------------------------------- 만들기
    def add(self, key: str, qualified_name: str, title: str, pos: tuple, settings: dict | None = None):
        desc = registry().widget(qualified_name)
        props = copy.deepcopy(settings) if settings else None
        if props is not None and "__version__" not in props:
            # 버전 표시가 없으면 Orange가 '옛 설정'으로 보고 이전(migrate)한다 — 예: Test and Score의 resampling 번호가 밀린다
            props["__version__"] = widget_class(qualified_name).settings_version
        node = self.scheme.new_node(desc, title=title, position=(float(pos[0]), float(pos[1])), properties=props)
        self.nodes[key] = node
        return self.w(key)

    def w(self, key: str):
        return self.scheme.widget_for_node(self.nodes[key])

    def link(self, src: str, out: str, dst: str, inp: str):
        s, d = self.nodes[src], self.nodes[dst]
        out_ch = next((c for c in s.output_channels() if out in (c.id, c.name)), None)
        in_ch = next((c for c in d.input_channels() if inp in (c.id, c.name)), None)
        if out_ch is None or in_ch is None:
            raise KeyError(f"채널 없음: {src}.{out} → {dst}.{inp}")
        return self.scheme.new_link(s, out_ch, d, in_ch)

    def note(self, rect: tuple, text: str, size: int | None = None):
        from orangecanvas.scheme import SchemeTextAnnotation

        font = dict(NOTE_FONT)
        if size:
            font["size"] = size
        self.scheme.add_annotation(SchemeTextAnnotation(tuple(float(x) for x in rect), text, "text/plain", font))

    def arrow(self, start: tuple, end: tuple, color: str = "#C1272D"):
        from orangecanvas.scheme import SchemeArrowAnnotation

        self.scheme.add_annotation(SchemeArrowAnnotation(tuple(map(float, start)), tuple(map(float, end)), color))

    # ----------------------------------------------------------- 실행
    def settle(self, timeout: float = 300.0, quiet: float = 1.0):
        return settle(self.scheme, timeout=timeout, quiet=quiet)

    # ----------------------------------------------------------- 저장
    def save(self, path: Path, scrub=None) -> Path:
        """캔버스의 '저장'과 같이 노드 설정을 위젯에서 다시 읽어 .ows로 쓴다. scrub(node_key, props) → props로 마지막 정리."""
        from orangecanvas.scheme.readwrite import scheme_to_ows_stream

        self.scheme.sync_node_properties()
        by_node = {node: key for key, node in self.nodes.items()}
        for node in self.scheme.nodes:
            props = dict(node.properties or {})
            props.pop("savedWidgetGeometry", None)
            props = to_builtin(scrub_paths(props))
            # Qt 값(예: Column Statistics의 정렬 Qt.SortOrder)은 저장하지 않는다 — 위젯이 자기 기본값을 쓴다(PyQt5·6 공통)
            for k in [k for k in props if k != "context_settings" and contains_qt(props[k])]:
                props.pop(k)
            if scrub is not None:
                props = scrub(by_node.get(node), props)
            node.properties = props
        buf = io.BytesIO()
        scheme_to_ows_stream(self.scheme, buf, pretty=True, pickle_fallback=True)
        data = buf.getvalue()
        assert_portable(data)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def close(self):
        try:
            self.scheme.clear()
        except Exception:  # noqa: BLE001
            pass
        process(0.05)


def settle(scheme, timeout: float = 300.0, quiet: float = 1.0) -> float:
    """신호 전달·백그라운드 계산이 모두 끝나 quiet초 동안 조용할 때까지 이벤트를 돌린다."""
    sm = scheme.signal_manager
    t0 = time.time()
    calm_since = None
    while time.time() - t0 < timeout:
        QCoreApplication.processEvents()
        busy = sm.has_pending()
        if not busy:
            for node in scheme.nodes:
                try:
                    if sm.is_blocking(node) or sm.is_invalidated(node):
                        busy = True
                        break
                    # Test and Score처럼 진행 막대(progressBarInit)로만 '계산 중'을 알리는 위젯
                    widget = scheme.widget_for_node(node)
                    if widget is not None and getattr(widget, "processingState", 0):
                        busy = True
                        break
                except Exception:  # noqa: BLE001
                    pass
        if busy:
            calm_since = None
        else:
            calm_since = calm_since or time.time()
            if time.time() - calm_since >= quiet:
                return time.time() - t0
        time.sleep(0.02)
    raise TimeoutError(f"워크플로가 {timeout:.0f}초 안에 멈추지 않았다")


# ---------------------------------------------------------------- 정리 · 이식성
def recent_path(relpath: str, sheet: str = "", file_format=None):
    """같은 폴더(basedir)의 파일을 가리키는 RecentPath. abspath는 파일 이름만 남긴다(만든 PC 경로 숨김)."""
    from orangewidget.utils.filedialogs import RecentPath

    return RecentPath(relpath, "basedir", relpath, title="", sheet=sheet, file_format=file_format)


def scrub_paths(props: dict) -> dict:
    """File 위젯의 recent_paths에서 절대 경로를 지우고 basedir 상대 경로만 남긴다."""
    from orangewidget.utils.filedialogs import RecentPath

    out = dict(props)
    if "recent_paths" in out:
        fixed = []
        for rp in out["recent_paths"]:
            if isinstance(rp, RecentPath) and rp.prefix == "basedir" and rp.relpath:
                fixed.append(RecentPath(rp.relpath, "basedir", rp.relpath, title=rp.title or "",
                                        sheet=rp.sheet or "", file_format=rp.file_format))
        out["recent_paths"] = fixed
    if "stored_path" in out:
        out["stored_path"] = "."
    return out


def contains_qt(obj) -> bool:
    mod = type(obj).__module__ or ""
    if mod.startswith(("PyQt", "AnyQt", "sip", "PySide")):
        return True
    if isinstance(obj, dict):
        return any(contains_qt(k) or contains_qt(v) for k, v in obj.items())
    if isinstance(obj, (list, tuple, set)):
        return any(contains_qt(v) for v in obj)
    return False


def to_builtin(obj):
    """numpy 수(np.float64 등)를 파이썬 기본형으로 — 피클이 numpy 1.x(numpy.core)·2.x(numpy._core) 어느 쪽에서도 열리게."""
    import numpy as np
    from orangewidget.settings import Context

    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {to_builtin(k): to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(to_builtin(v) for v in obj)
    if isinstance(obj, Context):
        for name, val in list(vars(obj).items()):
            setattr(obj, name, to_builtin(val))
        return obj
    return obj


_ABS = re.compile(rb"(/home/|/tmp/|/Users/|[A-Za-z]:\\\\)")


def assert_portable(ows_bytes: bytes):
    """피클에 Qt 객체가 없는지(PyQt5·PyQt6 설치판 모두 열림) · 만든 PC의 절대 경로가 없는지 확인한다."""
    import base64
    import xml.etree.ElementTree as ET

    root = ET.fromstring(ows_bytes)
    for prop in root.iter("properties"):
        text = (prop.text or "").strip()
        if prop.get("format") == "pickle":
            raw = base64.decodebytes(text.encode("ascii"))
            mods = set()
            for op, arg, _ in pickletools.genops(raw):
                if op.name in ("GLOBAL", "STACK_GLOBAL") and isinstance(arg, str):
                    mods.add(arg.split(" ")[0])
                if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE") and isinstance(arg, str) and (
                        "PyQt" in arg or "AnyQt" in arg or arg.startswith("Qt")):
                    mods.add(arg)
            bad = [m for m in mods if "PyQt" in m or "AnyQt" in m or m.startswith("Qt") or m.startswith("numpy")]
            if bad:
                raise AssertionError(f"node {prop.get('node_id')}: 피클에 Qt·numpy 객체 {bad}")
            if _ABS.search(raw):
                raise AssertionError(f"node {prop.get('node_id')}: 절대 경로가 남았다")
        elif _ABS.search(text.encode("utf-8")):
            raise AssertionError(f"node {prop.get('node_id')}: 절대 경로가 남았다")


# ---------------------------------------------------------------- 다시 열기 · 실행
def load_check(path: Path) -> dict:
    """새 Scheme로 다시 읽는다 — 알 수 없는 위젯·잘못된 채널이 있으면 예외."""
    from orangecanvas.scheme import Scheme
    from orangecanvas.scheme.readwrite import scheme_load

    errors = []
    scheme = Scheme()
    with open(path, "rb") as f:
        scheme_load(scheme, f, registry=registry(), error_handler=errors.append)
    if errors:
        raise AssertionError(f"{path.name}: 다시 열기 오류 {errors}")
    return {"nodes": len(scheme.nodes), "links": len(scheme.links), "annotations": len(scheme.annotations),
            "titles": [n.title for n in scheme.nodes]}


def run_ows(ows: Path, data_files: list[Path], workdir: Path, timeout: float = 600.0):
    """수강생 PC처럼: .ows와 데이터를 한 폴더에 두고 열어 끝까지 실행한다. (scheme, {title: widget})."""
    from orangecanvas.scheme.readwrite import scheme_load
    from orangecanvas.scheme.widgetmanager import WidgetManager
    from orangewidget.workflow.widgetsscheme import WidgetsScheme

    app()
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    local = workdir / ows.name
    shutil.copy2(ows, local)
    for f in data_files:
        shutil.copy2(f, workdir / Path(f).name)
    scheme = WidgetsScheme()
    scheme.set_runtime_env("basedir", str(workdir))
    scheme.widget_manager.set_creation_policy(WidgetManager.Immediate)
    errors = []
    with open(local, "rb") as f:
        scheme_load(scheme, f, registry=registry(), error_handler=errors.append)
    if errors:
        raise AssertionError(f"{ows.name}: 열기 오류 {errors}")
    settle(scheme, timeout=timeout)
    widgets = {n.title: scheme.widget_for_node(n) for n in scheme.nodes}
    return scheme, widgets


def link_value(scheme, src_title: str, out: str):
    """연결선에 실려 있는 값(= 그 위젯이 마지막으로 보낸 출력). 연결되지 않은 출력은 None."""
    for link in scheme.links:
        if link.source_node.title == src_title and out in (link.source_channel.id, link.source_channel.name):
            contents = scheme.signal_manager.link_contents(link)
            if contents:
                val = list(contents.values())[-1]
                from orangecanvas.scheme.signalmanager import LazyValue

                if LazyValue.is_lazy(val):  # Predictions 등은 '필요할 때 계산'하는 값을 보낸다
                    val = val.get_value()
                return val
    return None


def set_roles(file_widget, roles: dict[str, str], types: dict[str, str] | None = None):
    """File 위젯 열 표에서 역할(feature/target/meta/skip)·형식(categorical/numeric/text/datetime)을 바꾸고 Apply."""
    model = file_widget.domain_editor.model()
    names = [row[0] for row in model.variables]
    for name, tpe in (types or {}).items():
        model.setData(model.index(names.index(name), 1), tpe, Qt.EditRole)
    for name, place in roles.items():
        model.setData(model.index(names.index(name), 2), place, Qt.EditRole)
    file_widget.apply_button.click()


def domain_summary(table) -> dict:
    d = table.domain
    return {"rows": len(table), "class": [v.name for v in d.class_vars],
            "metas": [v.name for v in d.metas], "n_features": len(d.attributes)}
