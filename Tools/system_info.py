import os
import sys
import platform
import socket
import shutil
import ctypes

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def _obter_marca_cpu():
    """Tenta obter o nome comercial da CPU no Windows via registro; fallback multiplataforma."""
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            nome, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            if nome and nome.strip():
                return nome.strip()
        except Exception:
            pass
    proc = platform.processor()
    if proc and proc.strip():
        return proc.strip()
    return os.environ.get("PROCESSOR_IDENTIFIER", "Processador Desconhecido")


def _obter_info_memoria():
    """Retorna dados de memória RAM em GB e percentual de uso."""
    if HAS_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            used_gb = mem.used / (1024 ** 3)
            avail_gb = mem.available / (1024 ** 3)
            percent = mem.percent
            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "avail_gb": round(avail_gb, 2),
                "percent": round(percent, 1),
            }
        except Exception:
            pass

    # Fallback no Windows via ctypes
    if platform.system() == "Windows":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            used_gb = total_gb - avail_gb
            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "avail_gb": round(avail_gb, 2),
                "percent": round(stat.dwMemoryLoad, 1),
            }
        except Exception:
            pass

    return {
        "total_gb": 0.0,
        "used_gb": 0.0,
        "avail_gb": 0.0,
        "percent": 0.0,
    }


def _obter_info_disco(path="."):
    """Retorna informações de disco da partição atual."""
    try:
        if HAS_PSUTIL:
            d = psutil.disk_usage(path)
            return {
                "total_gb": round(d.total / (1024 ** 3), 2),
                "used_gb": round(d.used / (1024 ** 3), 2),
                "free_gb": round(d.free / (1024 ** 3), 2),
                "percent": round(d.percent, 1),
            }
        else:
            d = shutil.disk_usage(path)
            total = d.total / (1024 ** 3)
            free = d.free / (1024 ** 3)
            used = total - free
            pct = (used / total * 100) if total > 0 else 0
            return {
                "total_gb": round(total, 2),
                "used_gb": round(used, 2),
                "free_gb": round(free, 2),
                "percent": round(pct, 1),
            }
    except Exception:
        return {"total_gb": 0.0, "used_gb": 0.0, "free_gb": 0.0, "percent": 0.0}


def _versao_pacote(nome_pacote):
    """Obtém a versão de um pacote se instalado."""
    try:
        mod = __import__(nome_pacote)
        return getattr(mod, "__version__", "Instalado")
    except Exception:
        return "Não instalado"


def obter_informacoes_sistema():
    """
    Coleta informações completas da máquina (hardware e SO) e do ambiente de software.
    Retorna um dicionário estruturado.
    """
    # ── MÁQUINA / HARDWARE ──
    hostname = socket.gethostname()
    sistema_op = f"{platform.system()} {platform.release()}"
    build_so = platform.version()
    arquitetura = f"{platform.machine()} ({platform.architecture()[0]})"
    cpu_brand = _obter_marca_cpu()

    nucleos_fisicos = None
    nucleos_logicos = os.cpu_count() or 1
    cpu_freq_mhz = None
    cpu_uso_pct = None

    if HAS_PSUTIL:
        try:
            nucleos_fisicos = psutil.cpu_count(logical=False)
            nucleos_logicos = psutil.cpu_count(logical=True) or nucleos_logicos
            freq = psutil.cpu_freq()
            if freq:
                cpu_freq_mhz = round(freq.current, 1)
            cpu_uso_pct = psutil.cpu_percent(interval=0.05)
        except Exception:
            pass

    memoria = _obter_info_memoria()
    disco = _obter_info_disco()

    # ── SOFTWARE / AMBIENTE ──
    python_ver = sys.version.split()[0]
    python_impl = platform.python_implementation()

    # Solvers PuLP
    pulp_ver = _versao_pacote("pulp")
    solvers_disponiveis = []
    try:
        import pulp
        solvers_disponiveis = pulp.listSolvers(onlyAvailable=True)
    except Exception:
        pass

    pacotes = {
        "Streamlit": _versao_pacote("streamlit"),
        "PuLP": pulp_ver,
        "NumPy": _versao_pacote("numpy"),
        "Pandas": _versao_pacote("pandas"),
        "SciPy": _versao_pacote("scipy"),
        "SQLAlchemy": _versao_pacote("sqlalchemy"),
        "Plotly": _versao_pacote("plotly"),
        "PyDeck": _versao_pacote("pydeck"),
        "Numba": _versao_pacote("numba"),
    }

    return {
        "hardware": {
            "hostname": hostname,
            "sistema_operacional": sistema_op,
            "build_so": build_so,
            "arquitetura": arquitetura,
            "cpu_nome": cpu_brand,
            "nucleos_fisicos": nucleos_fisicos,
            "nucleos_logicos": nucleos_logicos,
            "cpu_freq_mhz": cpu_freq_mhz,
            "cpu_uso_pct": cpu_uso_pct,
            "ram_total_gb": memoria["total_gb"],
            "ram_usada_gb": memoria["used_gb"],
            "ram_disponivel_gb": memoria["avail_gb"],
            "ram_uso_pct": memoria["percent"],
            "disco_total_gb": disco["total_gb"],
            "disco_livre_gb": disco["free_gb"],
            "disco_usado_gb": disco["used_gb"],
            "disco_uso_pct": disco["percent"],
        },
        "software": {
            "python_versao": python_ver,
            "python_implementacao": python_impl,
            "solvers_disponiveis": solvers_disponiveis,
            "pacotes": pacotes,
        }
    }


def renderizar_caixa_sistema(titulo="💻 Informações da Máquina e Ambiente de Software", expandido=False):
    """
    Renderiza na interface Streamlit uma caixa estilizada contendo
    todas as informações de hardware da máquina e de software.
    """
    if not HAS_STREAMLIT:
        return

    info = obter_informacoes_sistema()
    hw = info["hardware"]
    sw = info["software"]

    # Nome resumido da CPU para caber bem no card
    cpu_nome_curto = hw["cpu_nome"]
    if "@" in cpu_nome_curto:
        cpu_nome_curto = cpu_nome_curto.split("@")[0].strip()

    solver_principal = (
        sw["solvers_disponiveis"][0]
        if sw["solvers_disponiveis"]
        else "Nenhum solver detectado"
    )

    with st.container(border=True):
        st.markdown(f"#### {titulo}")

        # Linha de métricas de destaque
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            label="🖥️ Processador",
            value=f"{hw['nucleos_logicos']} threads" + (f" ({hw['nucleos_fisicos']} núcleos)" if hw['nucleos_fisicos'] else ""),
            delta=cpu_nome_curto,
            delta_color="off"
        )
        c2.metric(
            label="🧠 Memória RAM",
            value=f"{hw['ram_total_gb']} GB",
            delta=f"{hw['ram_uso_pct']}% em uso ({hw['ram_disponivel_gb']} GB livres)",
            delta_color="off"
        )
        c3.metric(
            label="💻 Sistema & Máquina",
            value=hw["sistema_operacional"],
            delta=f"{hw['hostname']} • {hw['arquitetura']}",
            delta_color="off"
        )
        c4.metric(
            label="🐍 Python & Solver",
            value=f"Python {sw['python_versao']}",
            delta=f"PuLP ({solver_principal})",
            delta_color="off"
        )

        with st.expander("🔍 Ver especificações detalhadas de Hardware e Software", expanded=expandido):
            col_hw, col_sw = st.columns(2)

            with col_hw:
                st.markdown("##### 🖥️ Hardware e Sistema Operacional")
                df_hw = [
                    ("Nome do Host", hw["hostname"]),
                    ("Sistema Operacional", hw["sistema_operacional"]),
                    ("Build do SO", hw["build_so"]),
                    ("Arquitetura", hw["arquitetura"]),
                    ("Processador", hw["cpu_nome"]),
                    ("Núcleos Físicos", str(hw["nucleos_fisicos"]) if hw["nucleos_fisicos"] else "N/A"),
                    ("Threads Lógicos", str(hw["nucleos_logicos"])),
                    ("Frequência da CPU", f"{hw['cpu_freq_mhz']} MHz" if hw["cpu_freq_mhz"] else "N/A"),
                    ("Uso Atual de CPU", f"{hw['cpu_uso_pct']}%" if hw["cpu_uso_pct"] is not None else "N/A"),
                    ("Memória RAM Total", f"{hw['ram_total_gb']} GB"),
                    ("Memória RAM em Uso", f"{hw['ram_usada_gb']} GB ({hw['ram_uso_pct']}%)"),
                    ("Memória RAM Disponível", f"{hw['ram_disponivel_gb']} GB"),
                    ("Armazenamento Total", f"{hw['disco_total_gb']} GB"),
                    ("Armazenamento Livre", f"{hw['disco_livre_gb']} GB ({100 - hw['disco_uso_pct']:.1f}% livre)"),
                ]
                import pandas as pd
                st.dataframe(
                    pd.DataFrame(df_hw, columns=["Componente / Parâmetro", "Valor"]),
                    hide_index=True,
                    width="stretch"
                )

            with col_sw:
                st.markdown("##### ⚙️ Software, Solvers e Bibliotecas")
                df_sw = [
                    ("Versão do Python", f"{sw['python_versao']} ({sw['python_implementacao']})"),
                    ("Solvers de Otimização", ", ".join(sw["solvers_disponiveis"]) if sw["solvers_disponiveis"] else "Nenhum"),
                ]
                for pacote, versao in sw["pacotes"].items():
                    df_sw.append((f"Biblioteca: {pacote}", str(versao)))

                import pandas as pd
                st.dataframe(
                    pd.DataFrame(df_sw, columns=["Item / Biblioteca", "Versão / Status"]),
                    hide_index=True,
                    width="stretch"
                )
