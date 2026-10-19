import os
import re
import subprocess
import tempfile
from pathlib import Path

import streamlit as st
import imageio_ffmpeg
from gtts import gTTS

st.set_page_config(page_title="Myanmar Movie Recap Maker", page_icon="🎬", layout="centered")

st.title("🎬 Myanmar Movie Recap Maker")
st.caption("Android ဖုန်းကနေ Movie Recap Video ပြုလုပ်ရန်")

st.info(
    "ဒီ MVP ဗားရှင်းက ဗီဒီယိုကို အချိန်ပိုင်းညီညီ အလိုအလျောက်ရွေးပြီး ဆက်ပေးပါတယ်။ "
    "ဇာတ်လမ်းကို AI နဲ့ နားလည်ပြီး အကျဉ်းချုပ်ရေးပေးတဲ့စနစ် မပါသေးပါ။ "
    "မြန်မာအသံဖန်တီးဖို့ အင်တာနက်လိုပါတယ်။"
)

uploaded = st.file_uploader("ကိုယ်ပိုင်/အသုံးပြုခွင့်ရှိတဲ့ ရုပ်ရှင်ဗီဒီယိုကို ရွေးပါ", type=["mp4", "mov", "mkv", "webm"])
target_minutes = st.selectbox("Recap အရှည်", [1, 3, 5, 10], index=2)
clip_seconds = st.slider("တစ်နေရာစီမှ ယူမယ့်အချိန် (စက္ကန့်)", min_value=5, max_value=30, value=15, step=1)
voiceover = st.text_area(
    "မြန်မာဇာတ်ကြောင်းဖတ်စာသား",
    value="ဒီနေ့မှာ စိတ်ဝင်စားဖွယ် ရုပ်ရှင်ဇာတ်လမ်းတစ်ပုဒ်ကို အကျဉ်းချုပ် တင်ဆက်ပေးသွားမှာ ဖြစ်ပါတယ်။ "
          "ဇာတ်လမ်းရဲ့ အရေးကြီးတဲ့အခိုက်အတန့်တွေကို အတူတူ ကြည့်ရှုလိုက်ကြရအောင်။",
    height=130,
    help="ပထမဗားရှင်းမှာ ဇာတ်ကြောင်းစာသားကို ကိုယ်တိုင်ထည့်ပါ။ AI အလိုအလျောက်ရေးပေးခြင်းကို နောက်ဗားရှင်းတွင် ချိတ်ဆက်နိုင်ပါတယ်။"
)
make_voice = st.checkbox("မြန်မာအသံဖတ်သံ ထည့်ရန် (အင်တာနက်လို)", value=True)

def run_cmd(args, timeout=1800):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="ignore")[-2500:]
        raise RuntimeError(err or "Video processing မအောင်မြင်ပါ။")
    return result

def get_duration(ffmpeg, path):
    p = subprocess.run([ffmpeg, "-i", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = p.stderr.decode("utf-8", errors="ignore")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", info)
    if not match:
        raise RuntimeError("Video အရှည်ကို မဖတ်နိုင်ပါ။ MP4 ဖိုင်နဲ့ ပြန်စမ်းပါ။")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

if uploaded and st.button("✨ Recap Video ဖန်တီးမယ်", type="primary", use_container_width=True):
    if not voiceover.strip() and make_voice:
        st.error("မြန်မာအသံဖတ်စာသားကို ထည့်ပေးပါ။")
        st.stop()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    progress = st.progress(0, text="ဗီဒီယိုကို ပြင်ဆင်နေပါတယ်...")
    status = st.empty()

    try:
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            input_path = work / ("source" + Path(uploaded.name).suffix.lower())
            input_path.write_bytes(uploaded.getvalue())

            duration = get_duration(ffmpeg, input_path)
            desired = min(target_minutes * 60, max(1, int(duration)))
            segment = min(clip_seconds, desired)
            # Choose short clips from evenly spaced positions across the source.
            count = max(1, min(20, int((desired + segment - 1) // segment)))
            if count == 1:
                starts = [max(0, (duration - segment) / 2)]
            else:
                last_start = max(0, duration - segment)
                starts = [last_start * i / (count - 1) for i in range(count)]

            parts = []
            for i, start in enumerate(starts):
                part = work / f"part_{i:02d}.mp4"
                run_cmd([
                    ffmpeg, "-y", "-ss", str(start), "-i", str(input_path),
                    "-t", str(segment), "-vf", "scale='min(1280,iw)':-2",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                    str(part)
                ])
                parts.append(part)
                progress.progress(int(10 + 55 * (i + 1) / len(starts)), text=f"အပိုင်း {i+1}/{len(starts)} ပြုလုပ်နေပါတယ်...")

            list_file = work / "concat.txt"
            list_file.write_text("".join("file '" + str(p).replace("'", "'\\''") + "'\n" for p in parts), encoding="utf-8")
            joined = work / "joined.mp4"
            run_cmd([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
                     "-c", "copy", str(joined)])
            final_path = work / "myanmar_movie_recap.mp4"

            if make_voice:
                status.info("မြန်မာအသံဖတ်သံ ဖန်တီးနေပါတယ်...")
                voice_path = work / "voice.mp3"
                # gTTS language support depends on the installed service/language list.
                gTTS(text=voiceover.strip(), lang="my", slow=False).save(str(voice_path))
                run_cmd([
                    ffmpeg, "-y", "-i", str(joined), "-i", str(voice_path),
                    "-filter_complex", "[0:a]volume=0.22[bg];[1:a]volume=1.0[vo];[bg][vo]amix=inputs=2:duration=first:dropout_transition=2[a]",
                    "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "128k", "-movflags", "+faststart", str(final_path)
                ])
            else:
                joined.replace(final_path)

            output_bytes = final_path.read_bytes()
            progress.progress(100, text="ပြီးပါပြီ!")
            status.success("Recap Video ဖန်တီးပြီးပါပြီ။")
            st.video(output_bytes)
            st.download_button(
                "⬇️ MP4 ဖိုင် ဒေါင်းလုဒ်လုပ်မယ်",
                data=output_bytes,
                file_name="myanmar_movie_recap.mp4",
                mime="video/mp4",
                use_container_width=True
            )
            st.caption("သတိပြုရန် — အရင်းအမြစ်ဗီဒီယိုကြီးလွန်းလျှင် Render ရဲ့ memory/time ကန့်သတ်ချက်ကြောင့် မအောင်မြင်နိုင်ပါ။")
    except Exception as exc:
        st.error("ဖန်တီးမှု မအောင်မြင်ပါ။")
        st.code(str(exc))
        st.warning("အရင်ဆုံး MP4 ဖိုင်သေးသေးတစ်ခုနဲ့ စမ်းပါ။ မြန်မာအသံအပိုင်း error ဖြစ်လျှင် 'မြန်မာအသံဖတ်သံ ထည့်ရန်' ကို ဖြုတ်ပြီး video processing ကို စမ်းနိုင်ပါတယ်။")

st.divider()
st.caption("ကိုယ်ပိုင်ဖန်တီးထားသော သို့မဟုတ် အသုံးပြုခွင့်ရှိသော ဗီဒီယိုများကိုသာ တင်ပါ။")
