"""
SIMAK - Sistem Informasi Manajemen Asesmen Kompetensi
Web app sederhana berbasis Flask + JSON sebagai penyimpanan data.

Fitur:
A. Autentikasi
B. Dashboard
C. Manajemen Data Peserta
D. Jadwal Asesmen
E. Input Penilaian Kompetensi
F. Rekap & Laporan Hasil
G. Profil Asesor
"""

import json
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)
app.secret_key = "ganti-dengan-secret-key-anda-sendiri"  # ganti saat produksi


# ---------------------------------------------------------------------------
# Util penyimpanan JSON
# ---------------------------------------------------------------------------
def _path(name):
    return os.path.join(DATA_DIR, f"{name}.json")


def load_data(name):
    path = _path(name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(name, data):
    path = _path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(items):
    return (max([i["id"] for i in items], default=0)) + 1


# Inisialisasi password default (asesor1 / asesor123) jika masih placeholder
def ensure_default_password():
    users = load_data("users")
    changed = False
    for u in users:
        if u.get("password_hash", "").endswith("placeholder"):
            u["password_hash"] = generate_password_hash("asesor123")
            changed = True
    if changed:
        save_data("users", users)


ensure_default_password()


# ---------------------------------------------------------------------------
# A. AUTENTIKASI
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if "user_id" not in session:
        return None
    users = load_data("users")
    return next((u for u in users if u["id"] == session["user_id"]), None)


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_data("users")
        user = next((u for u in users if u["username"] == username), None)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["nama"] = user["nama"]
            flash(f"Selamat datang, {user['nama']}.", "success")
            return redirect(url_for("dashboard"))
        flash("Username atau password salah.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah keluar dari sistem.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# B. DASHBOARD
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    peserta = load_data("peserta")
    jadwal = load_data("jadwal")
    penilaian = load_data("penilaian")

    today = datetime.now().strftime("%Y-%m-%d")
    jadwal_mendatang = sorted(
        [j for j in jadwal if j["tanggal"] >= today and j["status"] == "Terjadwal"],
        key=lambda x: (x["tanggal"], x["waktu"])
    )[:5]

    def peserta_nama(pid):
        p = next((p for p in peserta if p["id"] == pid), None)
        return p["nama"] if p else "-"

    for j in jadwal_mendatang:
        j["peserta_nama"] = peserta_nama(j["peserta_id"])

    total_kompeten = sum(1 for p in penilaian if p.get("rekomendasi") == "Kompeten")
    total_belum_kompeten = sum(1 for p in penilaian if p.get("rekomendasi") == "Belum Kompeten")

    stats = {
        "total_peserta": len(peserta),
        "total_jadwal": len(jadwal),
        "jadwal_terjadwal": sum(1 for j in jadwal if j["status"] == "Terjadwal"),
        "total_penilaian": len(penilaian),
        "total_kompeten": total_kompeten,
        "total_belum_kompeten": total_belum_kompeten,
    }

    return render_template(
        "dashboard.html", stats=stats, jadwal_mendatang=jadwal_mendatang
    )


# ---------------------------------------------------------------------------
# C. MANAJEMEN DATA PESERTA
# ---------------------------------------------------------------------------
@app.route("/peserta")
@login_required
def peserta_list():
    q = request.args.get("q", "").strip().lower()
    peserta = load_data("peserta")
    if q:
        peserta = [
            p for p in peserta
            if q in p["nama"].lower()
            or q in p.get("instansi", "").lower()
            or q in p.get("skema_sertifikasi", "").lower()
        ]
    return render_template("peserta_list.html", peserta=peserta, q=q)


@app.route("/peserta/tambah", methods=["GET", "POST"])
@login_required
def peserta_tambah():
    if request.method == "POST":
        peserta = load_data("peserta")
        new_item = {
            "id": next_id(peserta),
            "nama": request.form.get("nama", "").strip(),
            "nik": request.form.get("nik", "").strip(),
            "no_hp": request.form.get("no_hp", "").strip(),
            "email": request.form.get("email", "").strip(),
            "instansi": request.form.get("instansi", "").strip(),
            "jabatan": request.form.get("jabatan", "").strip(),
            "skema_sertifikasi": request.form.get("skema_sertifikasi", "").strip(),
            "status": request.form.get("status", "Aktif"),
        }
        peserta.append(new_item)
        save_data("peserta", peserta)
        flash("Data peserta berhasil ditambahkan.", "success")
        return redirect(url_for("peserta_list"))
    return render_template("peserta_form.html", peserta=None)


@app.route("/peserta/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def peserta_edit(pid):
    peserta = load_data("peserta")
    item = next((p for p in peserta if p["id"] == pid), None)
    if not item:
        flash("Data peserta tidak ditemukan.", "danger")
        return redirect(url_for("peserta_list"))

    if request.method == "POST":
        item.update({
            "nama": request.form.get("nama", "").strip(),
            "nik": request.form.get("nik", "").strip(),
            "no_hp": request.form.get("no_hp", "").strip(),
            "email": request.form.get("email", "").strip(),
            "instansi": request.form.get("instansi", "").strip(),
            "jabatan": request.form.get("jabatan", "").strip(),
            "skema_sertifikasi": request.form.get("skema_sertifikasi", "").strip(),
            "status": request.form.get("status", "Aktif"),
        })
        save_data("peserta", peserta)
        flash("Data peserta berhasil diperbarui.", "success")
        return redirect(url_for("peserta_list"))

    return render_template("peserta_form.html", peserta=item)


@app.route("/peserta/<int:pid>/hapus", methods=["POST"])
@login_required
def peserta_hapus(pid):
    peserta = load_data("peserta")
    peserta = [p for p in peserta if p["id"] != pid]
    save_data("peserta", peserta)
    flash("Data peserta berhasil dihapus.", "info")
    return redirect(url_for("peserta_list"))


# ---------------------------------------------------------------------------
# D. JADWAL ASESMEN
# ---------------------------------------------------------------------------
def enrich_jadwal(jadwal, peserta, users):
    for j in jadwal:
        p = next((p for p in peserta if p["id"] == j["peserta_id"]), None)
        a = next((u for u in users if u["id"] == j["asesor_id"]), None)
        j["peserta_nama"] = p["nama"] if p else "-"
        j["asesor_nama"] = a["nama"] if a else "-"
    return jadwal


@app.route("/jadwal")
@login_required
def jadwal_list():
    jadwal = load_data("jadwal")
    peserta = load_data("peserta")
    users = load_data("users")
    jadwal = enrich_jadwal(jadwal, peserta, users)
    jadwal.sort(key=lambda x: (x["tanggal"], x["waktu"]))
    return render_template("jadwal_list.html", jadwal=jadwal)


@app.route("/jadwal/tambah", methods=["GET", "POST"])
@login_required
def jadwal_tambah():
    peserta = load_data("peserta")
    if request.method == "POST":
        jadwal = load_data("jadwal")
        new_item = {
            "id": next_id(jadwal),
            "peserta_id": int(request.form.get("peserta_id")),
            "asesor_id": session["user_id"],
            "skema": request.form.get("skema", "").strip(),
            "tanggal": request.form.get("tanggal", ""),
            "waktu": request.form.get("waktu", ""),
            "tempat": request.form.get("tempat", "").strip(),
            "status": "Terjadwal",
        }
        jadwal.append(new_item)
        save_data("jadwal", jadwal)
        flash("Jadwal asesmen berhasil ditambahkan.", "success")
        return redirect(url_for("jadwal_list"))
    return render_template("jadwal_form.html", jadwal=None, peserta=peserta)


@app.route("/jadwal/<int:jid>/edit", methods=["GET", "POST"])
@login_required
def jadwal_edit(jid):
    jadwal = load_data("jadwal")
    item = next((j for j in jadwal if j["id"] == jid), None)
    peserta = load_data("peserta")
    if not item:
        flash("Jadwal tidak ditemukan.", "danger")
        return redirect(url_for("jadwal_list"))

    if request.method == "POST":
        item.update({
            "peserta_id": int(request.form.get("peserta_id")),
            "skema": request.form.get("skema", "").strip(),
            "tanggal": request.form.get("tanggal", ""),
            "waktu": request.form.get("waktu", ""),
            "tempat": request.form.get("tempat", "").strip(),
            "status": request.form.get("status", "Terjadwal"),
        })
        save_data("jadwal", jadwal)
        flash("Jadwal asesmen berhasil diperbarui.", "success")
        return redirect(url_for("jadwal_list"))

    return render_template("jadwal_form.html", jadwal=item, peserta=peserta)


@app.route("/jadwal/<int:jid>/hapus", methods=["POST"])
@login_required
def jadwal_hapus(jid):
    jadwal = load_data("jadwal")
    jadwal = [j for j in jadwal if j["id"] != jid]
    save_data("jadwal", jadwal)
    flash("Jadwal berhasil dihapus.", "info")
    return redirect(url_for("jadwal_list"))


# ---------------------------------------------------------------------------
# E. INPUT PENILAIAN KOMPETENSI
# ---------------------------------------------------------------------------
@app.route("/penilaian")
@login_required
def penilaian_list():
    jadwal = load_data("jadwal")
    peserta = load_data("peserta")
    users = load_data("users")
    penilaian = load_data("penilaian")

    jadwal = enrich_jadwal(jadwal, peserta, users)
    dinilai_ids = {p["jadwal_id"] for p in penilaian}
    for j in jadwal:
        j["sudah_dinilai"] = j["id"] in dinilai_ids

    jadwal.sort(key=lambda x: (x["tanggal"], x["waktu"]), reverse=True)
    return render_template("penilaian_list.html", jadwal=jadwal)


@app.route("/penilaian/<int:jid>/input", methods=["GET", "POST"])
@login_required
def penilaian_input(jid):
    jadwal = load_data("jadwal")
    item_jadwal = next((j for j in jadwal if j["id"] == jid), None)
    if not item_jadwal:
        flash("Jadwal tidak ditemukan.", "danger")
        return redirect(url_for("penilaian_list"))

    peserta = load_data("peserta")
    peserta_item = next((p for p in peserta if p["id"] == item_jadwal["peserta_id"]), None)

    penilaian = load_data("penilaian")
    existing = next((p for p in penilaian if p["jadwal_id"] == jid), None)

    if request.method == "POST":
        unit_kompetensi = request.form.getlist("unit_kompetensi[]")
        kriteria = request.form.getlist("kriteria[]")
        nilai = request.form.getlist("nilai[]")

        elemen = [
            {"unit_kompetensi": uk, "kriteria_unjuk_kerja": kk, "nilai": nv}
            for uk, kk, nv in zip(unit_kompetensi, kriteria, nilai)
            if uk.strip() or kk.strip()
        ]

        rekomendasi = request.form.get("rekomendasi", "Belum Kompeten")
        catatan = request.form.get("catatan", "").strip()

        data = {
            "jadwal_id": jid,
            "peserta_id": item_jadwal["peserta_id"],
            "asesor_id": session["user_id"],
            "elemen": elemen,
            "catatan": catatan,
            "rekomendasi": rekomendasi,
            "tanggal_input": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        if existing:
            data["id"] = existing["id"]
            penilaian = [data if p["id"] == existing["id"] else p for p in penilaian]
            flash("Penilaian kompetensi berhasil diperbarui.", "success")
        else:
            data["id"] = next_id(penilaian)
            penilaian.append(data)
            flash("Penilaian kompetensi berhasil disimpan.", "success")

        save_data("penilaian", penilaian)

        # tandai jadwal selesai
        for j in jadwal:
            if j["id"] == jid:
                j["status"] = "Selesai"
        save_data("jadwal", jadwal)

        return redirect(url_for("penilaian_list"))

    return render_template(
        "penilaian_form.html",
        jadwal=item_jadwal, peserta=peserta_item, existing=existing
    )


# ---------------------------------------------------------------------------
# F. REKAP & LAPORAN HASIL
# ---------------------------------------------------------------------------
@app.route("/laporan")
@login_required
def laporan():
    penilaian = load_data("penilaian")
    peserta = load_data("peserta")
    jadwal = load_data("jadwal")

    def get_peserta(pid):
        return next((p for p in peserta if p["id"] == pid), None)

    def get_jadwal(jid):
        return next((j for j in jadwal if j["id"] == jid), None)

    rekap = []
    for p in penilaian:
        ps = get_peserta(p["peserta_id"])
        jd = get_jadwal(p["jadwal_id"])
        rekap.append({
            "id": p["id"],
            "peserta_nama": ps["nama"] if ps else "-",
            "instansi": ps["instansi"] if ps else "-",
            "skema": jd["skema"] if jd else "-",
            "tanggal": jd["tanggal"] if jd else "-",
            "rekomendasi": p["rekomendasi"],
            "tanggal_input": p["tanggal_input"],
        })

    rekap.sort(key=lambda x: x["tanggal_input"], reverse=True)

    filter_status = request.args.get("status", "")
    if filter_status:
        rekap = [r for r in rekap if r["rekomendasi"] == filter_status]

    total = len(penilaian)
    kompeten = sum(1 for p in penilaian if p["rekomendasi"] == "Kompeten")
    belum = total - kompeten

    return render_template(
        "laporan.html", rekap=rekap, total=total,
        kompeten=kompeten, belum=belum, filter_status=filter_status
    )


@app.route("/laporan/<int:pid>/detail")
@login_required
def laporan_detail(pid):
    penilaian = load_data("penilaian")
    item = next((p for p in penilaian if p["id"] == pid), None)
    if not item:
        flash("Data penilaian tidak ditemukan.", "danger")
        return redirect(url_for("laporan"))

    peserta = load_data("peserta")
    jadwal = load_data("jadwal")
    users = load_data("users")

    ps = next((p for p in peserta if p["id"] == item["peserta_id"]), None)
    jd = next((j for j in jadwal if j["id"] == item["jadwal_id"]), None)
    asesor = next((u for u in users if u["id"] == item["asesor_id"]), None)

    return render_template(
        "laporan_detail.html", item=item, peserta=ps, jadwal=jd, asesor=asesor
    )


# ---------------------------------------------------------------------------
# G. PROFIL ASESOR
# ---------------------------------------------------------------------------
@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    users = load_data("users")
    user = next((u for u in users if u["id"] == session["user_id"]), None)

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "biodata":
            user.update({
                "nama": request.form.get("nama", "").strip(),
                "no_reg": request.form.get("no_reg", "").strip(),
                "spesialisasi": request.form.get("spesialisasi", "").strip(),
                "email": request.form.get("email", "").strip(),
                "no_hp": request.form.get("no_hp", "").strip(),
                "instansi": request.form.get("instansi", "").strip(),
            })
            save_data("users", users)
            session["nama"] = user["nama"]
            flash("Profil berhasil diperbarui.", "success")

        elif form_type == "password":
            pw_lama = request.form.get("password_lama", "")
            pw_baru = request.form.get("password_baru", "")
            pw_konfirmasi = request.form.get("password_konfirmasi", "")

            if not check_password_hash(user["password_hash"], pw_lama):
                flash("Password lama salah.", "danger")
            elif pw_baru != pw_konfirmasi:
                flash("Konfirmasi password baru tidak cocok.", "danger")
            elif len(pw_baru) < 6:
                flash("Password baru minimal 6 karakter.", "danger")
            else:
                user["password_hash"] = generate_password_hash(pw_baru)
                save_data("users", users)
                flash("Password berhasil diperbarui.", "success")

        return redirect(url_for("profil"))

    return render_template("profil.html", user=user)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
