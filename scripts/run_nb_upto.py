"""노트북을 새 커널에서 위에서부터 N번째 코드 셀까지 실행하고 결과(출력)를 노트북에 저장한다.

실행: uv run python scripts/run_nb_upto.py <노트북 경로> <N>     (N = all 이면 전체 = 커널 재시작 후 전체 실행)
- 작업 폴더는 저장소 맨 위 폴더(노트북 안 경로 기준과 같다).
- N 뒤의 코드 셀은 출력을 비운다(아직 실행하지 않은 셀).
"""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

path, upto = Path(sys.argv[1]), sys.argv[2]
nb = nbformat.read(path, as_version=4)
code_idx = [i for i, c in enumerate(nb.cells) if c.cell_type == "code"]
n = len(code_idx) if upto == "all" else int(upto)

client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": "."}})
with client.setup_kernel():
    for k, i in enumerate(code_idx):
        cell = nb.cells[i]
        if k < n:
            client.execute_cell(cell, i)
            for out in cell.outputs:
                if out.output_type == "stream":
                    print(out.text, end="")
                elif out.output_type == "execute_result":
                    print(out.data.get("text/plain", ""))
                elif out.output_type == "error":
                    print("\n".join(out.traceback))
        else:
            cell.outputs, cell.execution_count = [], None

nbformat.write(nb, path)
print(f"\n[실행] 코드 셀 1~{n} / 전체 {len(code_idx)} → {path}")
