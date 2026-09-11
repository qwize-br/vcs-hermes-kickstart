#!/usr/bin/env python3
"""
Script para transcrever vídeos do YouTube
Uso: python transcribe.py <URL_DO_YOUTUBE>
"""

import sys
import argparse
import re
import os
import html
import tempfile
import subprocess
import json
import glob
import base64
from datetime import datetime
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import yt_dlp
from yt_dlp.utils import DownloadError
from openai import OpenAI
from dotenv import load_dotenv
from xml.etree.ElementTree import ParseError

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


def extract_video_id(url):
    """Extrai o ID do vídeo de uma URL do YouTube"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_transcript(video_id, target_lang="pt"):
    """Obtém a transcrição do vídeo"""
    try:
        # Lista todas as transcrições disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Mostra idiomas disponíveis
        available_transcripts = []
        for transcript in transcript_list:
            lang_info = f"{transcript.language} ({transcript.language_code})"
            if transcript.is_generated:
                lang_info += " [auto-gerada]"
            available_transcripts.append(lang_info)

        if available_transcripts:
            print(f"💬 Legendas disponíveis: {', '.join(available_transcripts)}")

        # Tenta pegar transcrição no idioma alvo primeiro, depois fallback
        transcript = None
        search_langs = [target_lang]
        if target_lang == 'pt':
            search_langs.append('pt-BR')
            
        try:
            transcript = transcript_list.find_transcript(search_langs)
            print(f"✓ Usando transcrição em {target_lang}")
        except:
            if target_lang != 'en':
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    print(f"✓ Usando transcrição em inglês (fallback)")
                except:
                    pass
            
            if not transcript:
                # Pega a primeira disponível (manual ou auto-gerada)
                for t in transcript_list:
                    transcript = t
                    print(f"✓ Usando transcrição em {t.language}")
                    break

        if transcript:
            try:
                return transcript.fetch()
            except ParseError as e:
                # O YouTube pode retornar corpo vazio/HTML, quebrando o parser interno do lib
                print(f"⚠️  Falha ao baixar legendas via youtube-transcript-api (ParseError: {e}).")
                return None
        else:
            return None

    except TranscriptsDisabled:
        print(f"❌ Erro: As transcrições estão desabilitadas para este vídeo.")
        print(f"   O vídeo pode não ter legendas disponíveis.")
        return None
    except NoTranscriptFound:
        print(f"❌ Erro: Nenhuma transcrição encontrada para este vídeo.")
        print(f"   O vídeo pode não ter legendas/closed captions habilitadas.")
        return None
    except Exception as e:
        print(f"❌ Erro ao obter transcrição: {e}")
        print(f"   Possíveis causas:")
        print(f"   - O vídeo pode estar privado ou removido")
        print(f"   - O vídeo pode não ter legendas disponíveis")
        print(f"   - Pode haver problemas de conexão com o YouTube")
        return None


def vtt_to_text(vtt_content: str) -> str:
    """Converte conteúdo WebVTT em texto simples."""
    if not vtt_content:
        return ""

    lines = vtt_content.splitlines()
    out_lines: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.upper() == "WEBVTT":
            continue
        if line.startswith("NOTE"):
            continue
        if "-->" in line:
            # timestamp line
            continue
        if re.fullmatch(r"\d+", line):
            # cue index
            continue

        # remove simple HTML-ish tags sometimes present in subtitles
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line)
        out_lines.append(line)

    text = " ".join(out_lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ytdlp_common_opts():
    """Opções padrão do yt-dlp (aceita cookies/proxy via env)."""
    cookies_file = os.getenv("YTDLP_COOKIES_FILE")
    proxy = os.getenv("YTDLP_PROXY")
    user_agent = os.getenv("YTDLP_USER_AGENT")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 1,
        "nocheckcertificate": True,
        "geo_bypass": True,
        # Tenta reduzir 403/variações de player
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "mweb"],
            }
        },
    }

    if cookies_file:
        opts["cookiefile"] = cookies_file
    if proxy:
        opts["proxy"] = proxy
    if user_agent:
        opts["http_headers"] = {"User-Agent": user_agent}

    return opts


def get_subtitles_text_with_ytdlp(video_id: str, url: str, prefer_langs=None) -> str | None:
    """
    Tenta obter legendas (manuais ou auto-geradas) via yt-dlp, sem baixar o vídeo.
    Retorna texto simples ou None.
    """
    prefer_langs = prefer_langs or ["pt", "pt-BR", "en"]

    print("📝 Tentando obter legendas via yt-dlp (fallback)...")

    # Importante: se pedirmos vários idiomas de uma vez, uma falha em um deles pode abortar tudo.
    # Então tentamos idioma por idioma.
    last_error: Exception | None = None

    for lang in prefer_langs:
        try:
            with tempfile.TemporaryDirectory(prefix=f"subs_{video_id}_") as tmpdir:
                out_base = str(Path(tmpdir) / f"subs_{video_id}.%(ext)s")
                ydl_opts = {
                    **_ytdlp_common_opts(),
                    "skip_download": True,
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitlesformat": "vtt",
                    "subtitleslangs": [lang],
                    "outtmpl": out_base,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                tmp_path = Path(tmpdir)
                candidates = sorted(tmp_path.glob("*.vtt"))
                if not candidates:
                    continue

                best = candidates[0]
                vtt = best.read_text(encoding="utf-8", errors="replace")
                text = vtt_to_text(vtt)
                if text:
                    return text

        except DownloadError as e:
            last_error = e
            msg = str(e)
            if "HTTP Error 429" in msg:
                print(f"⚠️  YouTube limitou requisições (429) ao tentar baixar legendas ({lang}).")
                # 429 geralmente é por IP/sem cookies; não faz sentido insistir muito.
                break
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        print(f"⚠️  Falha ao obter legendas via yt-dlp: {last_error}")
    return None


def download_audio(video_id, url):
    """Baixa o áudio do vídeo do YouTube"""
    try:
        print(f"🎵 Baixando áudio do vídeo...")

        output_path = f"temp_audio_{video_id}.mp3"

        ydl_opts = {
            **_ytdlp_common_opts(),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'temp_audio_{video_id}.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"✓ Áudio baixado com sucesso")
        return output_path

    except Exception as e:
        print(f"❌ Erro ao baixar áudio: {e}")
        return None


def get_audio_duration(audio_file: str) -> float:
    """Get duration of audio file in seconds using FFmpeg."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        audio_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])


def accelerate_audio(input_file: str, output_file: str, speed: float = 1.5) -> str:
    """Accelerate audio using FFmpeg atempo filter."""
    if speed < 0.5 or speed > 4.0:
        raise ValueError(f"Speed {speed} out of range (0.5-4.0)")

    # Build filter chain for speeds > 2.0
    if speed <= 2.0:
        filter_str = f"atempo={speed}"
    else:
        # Chain multiple atempo filters (e.g., 3.0x = 1.5x * 2.0x)
        factor1 = 2.0
        factor2 = speed / 2.0
        filter_str = f"atempo={factor1},atempo={factor2}"

    cmd = [
        'ffmpeg', '-i', input_file,
        '-filter:a', filter_str,
        '-vn',  # No video
        '-y',   # Overwrite
        output_file
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_file


def split_audio_into_chunks(audio_file: str, video_id: str, target_size_mb: float = 24.5) -> list[str]:
    """Split audio file into chunks under target size."""
    # Get file info
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    duration_sec = get_audio_duration(audio_file)

    # Calculate chunk duration with safety margin
    chunk_duration_sec = (target_size_mb / file_size_mb) * duration_sec * 0.95

    # Create output pattern
    output_pattern = f"temp_audio_{video_id}_chunk_%03d.mp3"

    cmd = [
        'ffmpeg', '-i', audio_file,
        '-f', 'segment',
        '-segment_time', str(chunk_duration_sec),
        '-c', 'copy',  # Copy codec (no re-encoding)
        '-y',
        output_pattern
    ]

    subprocess.run(cmd, capture_output=True, check=True)

    # Collect chunk files
    chunk_files = sorted(glob.glob(f"temp_audio_{video_id}_chunk_*.mp3"))
    return chunk_files


def transcribe_audio_chunks(chunk_files: list[str], language: str = "pt") -> str:
    """Transcribe multiple audio chunks and combine results."""
    results = []

    for i, chunk_file in enumerate(chunk_files, 1):
        print(f"📝 Transcrevendo chunk {i}/{len(chunk_files)}...")

        try:
            text = transcribe_with_whisper(chunk_file, language)
            if text:
                results.append(text)
            else:
                print(f"⚠️  Chunk {i} retornou transcrição vazia")
        except Exception as e:
            print(f"⚠️  Erro ao transcrever chunk {i}: {e}")
            # Continue with other chunks
        finally:
            # Clean up chunk file
            if os.path.exists(chunk_file):
                try:
                    os.remove(chunk_file)
                except:
                    pass

    return " ".join(results)


def transcribe_with_whisper_enhanced(audio_file: str, video_id: str, target_lang: str = "pt") -> str | None:
    """Enhanced GPT-4o Audio transcription with auto-chunking and acceleration."""
    temp_files = []

    try:
        # Get file size
        file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)

        # Path 1: Direct transcription (< 25MB)
        if file_size_mb < 25:
            return transcribe_with_whisper(audio_file, target_lang)

        # Path 2: Try acceleration for medium files (25-35MB)
        if file_size_mb < 35:
            print(f"📊 Arquivo excede 25MB ({file_size_mb:.1f}MB), tentando acelerar áudio...")
            accelerated_file = f"temp_audio_{video_id}_accelerated.mp3"
            temp_files.append(accelerated_file)

            try:
                accelerate_audio(audio_file, accelerated_file, speed=1.5)
                accel_size_mb = os.path.getsize(accelerated_file) / (1024 * 1024)

                if accel_size_mb < 25:
                    print(f"✓ Áudio acelerado para {accel_size_mb:.1f}MB")
                    return transcribe_with_whisper(accelerated_file, target_lang)
                else:
                    print(f"⚠️  Áudio acelerado ainda excede 25MB ({accel_size_mb:.1f}MB)")
            except Exception as e:
                print(f"⚠️  Falha ao acelerar áudio: {e}")

        # Path 3: Chunking (large files or acceleration failed)
        print(f"📊 Arquivo muito grande, dividindo em chunks...")

        # Try to accelerate first to reduce chunk count
        chunk_source = audio_file
        accelerated_file = f"temp_audio_{video_id}_accelerated.mp3"

        try:
            accelerate_audio(audio_file, accelerated_file, speed=1.5)
            chunk_source = accelerated_file
            temp_files.append(accelerated_file)
            print(f"✓ Áudio acelerado antes de dividir em chunks")
        except Exception as e:
            print(f"⚠️  Falha ao acelerar, usando arquivo original: {e}")

        # Split into chunks
        chunks = split_audio_into_chunks(chunk_source, video_id, target_size_mb=24.5)
        print(f"✓ Dividido em {len(chunks)} chunks")

        # Transcribe chunks (cleanup happens inside transcribe_audio_chunks)
        return transcribe_audio_chunks(chunks, language=target_lang)

    except Exception as e:
        print(f"❌ Erro ao transcrever com GPT-4o Audio: {e}")
        return None
    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


def transcribe_with_whisper(audio_file, target_lang="pt"):
    """Transcreve áudio usando GPT-4o Audio da OpenAI"""
    try:
        print(f"🤖 Transcrevendo áudio com GPT-4o Audio...")

        # Verifica se a API key está configurada
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print(f"❌ Erro: OPENAI_API_KEY não configurada.")
            print(f"   Configure com: export OPENAI_API_KEY='sua-chave-aqui'")
            return None

        client = OpenAI(api_key=api_key)

        # Lê e codifica o áudio em base64
        with open(audio_file, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode('utf-8')

        # Determina o nome do idioma para o prompt
        lang_map = {"pt": "português", "en": "inglês", "es": "espanhol"}
        lang_name = lang_map.get(target_lang, target_lang)

        # Usa GPT-4o Audio via chat completions com input de áudio
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_AUDIO_MODEL", "gpt-audio"),
            modalities=["text"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_data,
                                "format": "mp3"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Por favor, transcreva este áudio em {lang_name}. Retorne apenas o texto transcrito, sem comentários adicionais."
                        }
                    ]
                }
            ]
        )

        print(f"✓ Transcrição concluída com GPT-4o Audio")
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Erro ao transcrever com GPT-4o Audio: {e}")
        return None


def format_transcript(transcript_data):
    """Formata a transcrição em texto simples"""
    text = ""
    for entry in transcript_data:
        text += entry['text'] + " "

    # Limpa espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def save_transcript(video_id, transcript_text, method="legendas"):
    """Salva a transcrição em arquivo .md"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcricao_{video_id}_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Transcrição do Vídeo\n\n")
        f.write(f"**Video ID:** {video_id}\n")
        f.write(f"**URL:** https://www.youtube.com/watch?v={video_id}\n")
        f.write(f"**Método:** {method}\n")
        f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(transcript_text)
        f.write("\n")

    return filename


def main():
    parser = argparse.ArgumentParser(description="Script para transcrever vídeos do YouTube")
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument("--lang", "-l", help="Idioma preferencial para as legendas (ex: en, pt, es)", default="pt")
    
    args = parser.parse_args()
    url = args.url
    target_lang = args.lang

    print(f"🔍 Processando: {url} (Idioma: {target_lang})")

    # Extrai o ID do vídeo
    video_id = extract_video_id(url)
    if not video_id:
        print("❌ Erro: URL inválida. Por favor, forneça uma URL válida do YouTube.")
        sys.exit(1)

    print(f"📹 Video ID: {video_id}")

    # Tenta obter legendas primeiro
    print(f"📝 Tentando obter legendas do YouTube em '{target_lang}'...")
    transcript_data = get_transcript(video_id, target_lang)

    transcript_text = None
    method = "Legendas do YouTube"
    audio_file = None

    if transcript_data:
        # Se conseguiu legendas, formata
        transcript_text = format_transcript(transcript_data)
        method = "Legendas do YouTube (youtube-transcript-api)"
    else:
        # Fallback 1: tentar legendas via yt-dlp (sem baixar vídeo)
        prefer_langs = [target_lang]
        if target_lang == 'pt':
             prefer_langs.extend(["pt-BR", "en"])
        elif target_lang != 'en':
             prefer_langs.append("en")
             
        transcript_text = get_subtitles_text_with_ytdlp(video_id, url, prefer_langs=prefer_langs)
        if transcript_text:
            method = "Legendas do YouTube (yt-dlp)"
        else:
            # Fallback 2: GPT-4o Audio
            print("\n⚠️  Nenhuma legenda disponível. Usando GPT-4o Audio como fallback...")

            # Baixa o áudio
            audio_file = download_audio(video_id, url)
            if not audio_file:
                print("❌ Não foi possível baixar o áudio do vídeo.")
                sys.exit(1)

            # Transcreve com GPT-4o Audio
            transcript_text = transcribe_with_whisper_enhanced(audio_file, video_id, target_lang)
            method = "GPT-4o Audio (OpenAI)"

            # Remove arquivo de áudio temporário
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                    print(f"🗑️  Arquivo temporário removido")
                except:
                    print(f"⚠️  Não foi possível remover o arquivo temporário: {audio_file}")

    if not transcript_text:
        print("❌ Não foi possível obter a transcrição do vídeo.")
        sys.exit(1)

    # Salva em arquivo
    filename = save_transcript(video_id, transcript_text, method)

    print(f"\n✅ Transcrição salva em: {filename}")
    print(f"📊 Total de caracteres: {len(transcript_text)}")
    print(f"🔧 Método usado: {method}")


if __name__ == "__main__":
    main()
