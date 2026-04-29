#!/usr/bin/env python3
"""
aidoc — AIDOC AI-Native Document Format CLI Tool
Spec version: 0.1.0 | Tool version: 0.1.0

Usage:
    aidoc init [-o OUTPUT] [--title TITLE]
    aidoc create <file>... [-o OUTPUT] [--title TITLE] [--author AUTHOR] [--tags TAGS]
    aidoc md <file>
    aidoc ls <file>
    aidoc meta <file>
    aidoc info <file>
    aidoc check <file>
    aidoc extract <file> [output_dir]
    aidoc sign <file> --cert CERT --key KEY [--sm2] [--tsa URL]
    aidoc sign <file> --gen-key
    aidoc verify <file>
    aidoc --help
    aidoc --version

Examples:
    aidoc init -o mydoc.aidoc --title 'My Notes'
    aidoc create report.md -o report.aidoc --author '于申' --tags 'AI,架构'
    aidoc create doc.docx summary.md -o doc.aidoc
    aidoc md report.aidoc
    aidoc ls report.aidoc
    aidoc extract report.aidoc ./output
    aidoc sign report.aidoc --gen-key
    aidoc sign report.aidoc --cert cert.pem --key key.pem --tsa http://tsa.cn/timestamp
    aidoc verify report.aidoc
"""

import json
import os
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime

# ── 版本号 ──
# SPEC_VERSION: AIDOC 格式规范的版本（稳定，需经提案变更）
# __version__:    CLI 工具的版本（可随功能迭代频繁更新）
SPEC_VERSION = "0.1.0"
__version__ = "0.1.0"
MAGIC_MARKER = b"AIDOCv1"
STORE_EXTENSIONS = {'.docx', '.doc', '.pdf', '.xlsx', '.xls', '.pptx',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
                    '.mp4', '.mp3', '.zip', '.gz'}


# ═══════════════════════════════════════════════
#  Packer
# ═══════════════════════════════════════════════

def _should_store(path):
    ext = os.path.splitext(path)[1].lower()
    return ext in STORE_EXTENSIONS or ext == '.md'


def _get_compression(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.md' or ext in STORE_EXTENSIONS:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def _prepare_md_content(md_path, title):
    """读取或生成 content.md 的内容（确保是字符串）。"""
    if md_path:
        if not os.path.exists(md_path):
            _die(f"MD 文件不存在: {md_path}")
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return f"# {title}\n\n"


def pack(doc_path=None, md_path=None, output=None,
         title=None, author=None, tags=None, metadata=None, extra_files=None):
    """Pack files into an AIDOC container.

    核心约定：
      content.md 必须是 ZIP 中的第一个条目 —— 这是 AI 极速读取的基础。
    """
    if not title:
        if md_path:
            title = os.path.splitext(os.path.basename(md_path))[0]
        elif doc_path:
            title = os.path.splitext(os.path.basename(doc_path))[0]
        else:
            title = "Untitled"

    if not output:
        output = f"{title}.aidoc"

    meta = {
        "aidoc_version": SPEC_VERSION,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "author": author or "",
        "tags": tags or [],
    }
    if metadata:
        meta.update(metadata)

    # 预读取 MD 内容，确保它能作为第一个条目写入
    md_content = _prepare_md_content(md_path, title)
    md_bytes = md_content.encode('utf-8')

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.comment = MAGIC_MARKER

        # ── 第一条目：content.md（STORED，始终排第一）──
        # 使用 writestr + 手动构造 ZipInfo 确保：
        #   1. 无 data descriptor（CRC/大小均在 header 中）
        #   2. extra field 为空
        #   3. 文件名 = "content.md"（10 字节）
        # 这样数据偏移 = 30(header) + 10(filename) = 40（固定值）
        info = zipfile.ZipInfo('content.md')
        info.compress_type = zipfile.ZIP_STORED
        info.flag_bits = 0  # 无 data descriptor
        info.date_time = datetime.now().timetuple()[:6]
        zf.writestr(info, md_bytes)
        _log(f"📝 content.md            ({len(md_bytes):>8,} B)  [STORED]  ← 第 1 条目")

        # metadata.json (compressed)
        meta_bytes = json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8')
        zf.writestr('metadata.json', meta_bytes, zipfile.ZIP_DEFLATED)
        _log(f"📋 metadata.json         ({len(meta_bytes):>8,} B)  [DEFLATED]")

        # document.* (original files, stored)
        if doc_path:
            if not os.path.exists(doc_path):
                _die(f"文档不存在: {doc_path}")
            ext = os.path.splitext(doc_path)[1]
            compress = _get_compression(doc_path)
            mode = "STORED" if compress == zipfile.ZIP_STORED else "DEFLATED"
            zf.write(doc_path, f"document{ext}", compress_type=compress)
            size = os.path.getsize(doc_path)
            _log(f"📄 document{ext:7s}         ({size:>8,} B)  [{mode}]")

        # Extra files
        if extra_files:
            for src_path in extra_files:
                if not os.path.exists(src_path):
                    _log(f"⚠️  文件不存在，跳过: {src_path}")
                    continue
                arc_name = os.path.basename(src_path)
                compress = _get_compression(src_path)
                mode = "STORED" if compress == zipfile.ZIP_STORED else "DEFLATED"
                zf.write(src_path, arc_name, compress_type=compress)
                size = os.path.getsize(src_path)
                _log(f"📎 {arc_name:20s} ({size:>8,} B)  [{mode}]")

    _log(f"\n✅ 打包完成: {output} ({os.path.getsize(output):,} B)")


# ═══════════════════════════════════════════════
#  Reader
# ═══════════════════════════════════════════════

def is_valid(path):
    if not os.path.exists(path):
        return False
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            return zf.comment == MAGIC_MARKER
    except (zipfile.BadZipFile, IsADirectoryError):
        return False


def read_md_fast(path):
    """
    ⚡ AI 极速读取 content.md。

    原理：content.md 被约定为 ZIP 中的第一个条目，STORED 存储，
    无 data descriptor，无 extra field。

    因此数据偏移固定为：30 (local file header) + 10 ("content.md") = 40 字节。
    只需一次 seek + 一次 read，无需解析 ZIP 中央目录。

    这是 .aidoc 格式区别于普通 ZIP 的核心设计。
    """
    try:
        with open(path, 'rb') as f:
            # 读取 local file header（30 字节）
            header = f.read(30)
            if len(header) < 30:
                return None

            sig = struct.unpack('<I', header[0:4])[0]
            if sig != 0x04034b50:  # PK\x03\x04
                return None

            compress_method = struct.unpack('<H', header[8:10])[0]
            if compress_method != 0:  # 必须是 STORED
                return None

            flags = struct.unpack('<H', header[6:8])[0]
            if flags & 0x08:  # 有 data descriptor，回退到标准模式
                return None

            filename_len = struct.unpack('<H', header[26:28])[0]
            extra_len = struct.unpack('<H', header[28:30])[0]
            comp_size = struct.unpack('<I', header[18:22])[0]

            data_offset = 30 + filename_len + extra_len

            # 验证文件名是 content.md
            f.seek(30)
            filename = f.read(filename_len).decode('ascii')
            if filename != 'content.md':
                return None

            # 直接读取 MD 数据
            f.seek(data_offset)
            data = f.read(comp_size)
            return data.decode('utf-8-sig')
    except (OSError, UnicodeDecodeError):
        return None


def read_md(path):
    """
    标准读取 content.md（通过 ZIP 中央目录）。

    作为 read_md_fast 的安全回退方案。
    """
    with zipfile.ZipFile(path, 'r') as zf:
        try:
            return zf.read('content.md').decode('utf-8-sig')
        except KeyError:
            return None


def read_metadata(path):
    with zipfile.ZipFile(path, 'r') as zf:
        try:
            return json.loads(zf.read('metadata.json').decode('utf-8'))
        except KeyError:
            return None


def list_files(path):
    with zipfile.ZipFile(path, 'r') as zf:
        result = []
        for info in zf.infolist():
            result.append({
                'name': info.filename,
                'size': info.file_size,
                'compressed': info.compress_size,
                'compression': 'STORED' if info.compress_type == zipfile.ZIP_STORED else 'DEFLATED',
            })
        return result


def extract_file(path, member, output_dir='.'):
    with zipfile.ZipFile(path, 'r') as zf:
        os.makedirs(output_dir, exist_ok=True)
        return zf.extract(member, output_dir)


def extract_all(path, output_dir):
    with zipfile.ZipFile(path, 'r') as zf:
        os.makedirs(output_dir, exist_ok=True)
        zf.extractall(output_dir)
    return output_dir


# ═══════════════════════════════════════════════
#  Signing (数字证书签名)
# ═══════════════════════════════════════════════

# `_generate_self_signed_cert` 需要 cryptography
# 签名操作本身使用 openssl 命令行，确保 100% 兼容
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


SIGNATURE_FILES = {'manifest.json', 'signature.p7s', 'timestamp.tsr'}


def _compute_sha256(data):
    """计算 SHA-256 哈希。"""
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _read_entry_data(zf, name):
    """读取 ZIP 中指定条目的原始数据。"""
    return zf.read(name)


def _build_manifest(zf, skip_files=None):
    """为容器中所有文件（除 manifest/signature 自身外）构建 manifest。"""
    skip = set(SIGNATURE_FILES)
    if skip_files:
        skip.update(skip_files)

    entries = {}
    for info in zf.infolist():
        if info.filename in skip:
            continue
        data = zf.read(info.filename)
        entries[info.filename] = {
            'sha256': _compute_sha256(data),
            'size': info.file_size,
        }
    return entries


def _format_manifest(entries, algorithm='sha256'):
    """将 manifest 格式化为 JSON 字符串。"""
    manifest = {
        "aidoc_version": SPEC_VERSION,
        "manifest_version": "1.0",
        "algorithm": algorithm,
        "signed_at": datetime.now().isoformat(),
        "files": entries,
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')


def _get_openssl():
    """查找 openssl 可执行文件路径。"""
    import shutil
    openssl = shutil.which('openssl')
    if not openssl:
        return None
    return openssl


def sign_aidoc(path, cert_path=None, key_path=None, sm2=False, gen_key=False, tsa_url=None):
    """
    对 AIDOC 文件进行数字签名。

    内部添加 manifest.json（文件哈希清单）和 signature.p7s（PKCS#7 分离签名）。
    content.md 始终保持为第一个条目，不影响 AI 极速读取。
    """
    if not os.path.exists(path):
        _die(f"文件不存在: {path}")

    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")

    if gen_key:
        # 生成测试用自签名证书
        cert_path, key_path = _generate_self_signed_cert()
        _log(f"🔑 已生成测试证书: {cert_path}")

    if not cert_path or not key_path:
        _die("需要 --cert 和 --key 参数，或使用 --gen-key 生成测试证书")

    # 读取原始容器中的所有条目
    with zipfile.ZipFile(path, 'r') as zf:
        entries = []
        for info in zf.infolist():
            if info.filename in SIGNATURE_FILES:
                continue
            data = zf.read(info.filename)
            entries.append((info.filename, data, info.compress_type))

        # 构建 manifest（含所有文件的哈希）
        manifest_entries = _build_manifest(zf)

    # 序列化 manifest
    manifest_bytes = _format_manifest(manifest_entries)

    # 写入临时文件，用 openssl 签名
    import tempfile
    manifest_fd, manifest_path = tempfile.mkstemp(suffix='.json')
    os.write(manifest_fd, manifest_bytes)
    os.close(manifest_fd)

    sig_fd, sig_path = tempfile.mkstemp(suffix='.p7s')
    os.close(sig_fd)

    try:
        openssl = _get_openssl()
        if not openssl:
            _die("找不到 openssl，无法签名")

        if sm2:
            algo = "SM2"
            # SM2 签名需要额外配置
            sign_cmd = [openssl, 'smime', '-sign',
                        '-in', manifest_path,
                        '-out', sig_path,
                        '-signer', cert_path,
                        '-inkey', key_path,
                        '-outform', 'DER',
                        '-binary']
        else:
            algo = "RSA/ECDSA"
            sign_cmd = [openssl, 'smime', '-sign',
                        '-in', manifest_path,
                        '-out', sig_path,
                        '-signer', cert_path,
                        '-inkey', key_path,
                        '-outform', 'DER',
                        '-binary']

        result = subprocess.run(sign_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            _die(f"签名失败: {result.stderr.strip()}")

        with open(sig_path, 'rb') as f:
            signature = f.read()

        # 时间戳服务（可选）
        timestamp_tsr = None
        if tsa_url:
            _log(f"🕒 请求时间戳: {tsa_url}")
            tsq_fd, tsq_path = tempfile.mkstemp(suffix='.tsq')
            os.close(tsq_fd)
            tsr_fd, tsr_path = tempfile.mkstemp(suffix='.tsr')
            os.close(tsr_fd)

            try:
                # 生成时间戳查询
                tsq_cmd = [openssl, 'ts', '-query',
                           '-data', sig_path,
                           '-out', tsq_path,
                           '-sha256']
                r = subprocess.run(tsq_cmd, capture_output=True, text=True)
                if r.returncode != 0:
                    _die(f"时间戳查询生成失败: {r.stderr.strip()}")

                # 发送到 TSA 服务器
                import urllib.request
                with open(tsq_path, 'rb') as f:
                    req_data = f.read()
                req = urllib.request.Request(tsa_url, data=req_data,
                    headers={'Content-Type': 'application/timestamp-query'})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    tsr_data = resp.read()
                with open(tsr_path, 'wb') as f:
                    f.write(tsr_data)

                # 验证时间戳响应
                ts_verify = [openssl, 'ts', '-verify',
                             '-data', sig_path,
                             '-in', tsr_path,
                             '-CAfile', '/dev/null',  # 仅在有时
                             '-untrusted']
                r = subprocess.run(ts_verify, capture_output=True, text=True)
                if r.returncode == 0:
                    _log(f"  ✅ 时间戳验证通过")

                with open(tsr_path, 'rb') as f:
                    timestamp_tsr = f.read()
                _log(f"  📎 timestamp.tsr       ({len(timestamp_tsr):>8,} B)")
            except Exception as e:
                _log(f"  ⚠️  时间戳请求失败: {e}")
            finally:
                for p in [tsq_path, tsr_path]:
                    if os.path.exists(p):
                        os.unlink(p)
    finally:
        os.unlink(manifest_path)
        os.unlink(sig_path)

    # 重建 AIDOC 文件（保持 content.md 为第一个条目）
    tmp_path = path + ".tmp"
    with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.comment = MAGIC_MARKER

        # content.md 必须是第一个条目
        content_data = None
        other_entries = []
        for name, data, comp in entries:
            if name == 'content.md':
                content_data = (name, data, comp)
            else:
                other_entries.append((name, data, comp))

        # 写入 content.md（保持 STORED，排第一）
        if content_data:
            info = zipfile.ZipInfo('content.md')
            info.compress_type = zipfile.ZIP_STORED
            info.flag_bits = 0
            info.date_time = datetime.now().timetuple()[:6]
            zf.writestr(info, content_data[1])
        else:
            _die("容器中没有 content.md，无法签名")

        # 写入其他原有文件
        for name, data, comp in other_entries:
            info = zipfile.ZipInfo(name)
            info.compress_type = comp
            info.flag_bits = 0
            info.date_time = datetime.now().timetuple()[:6]
            zf.writestr(info, data)

        # 写入 manifest.json
        zf.writestr('manifest.json', manifest_bytes, zipfile.ZIP_DEFLATED)
        _log(f"📋 manifest.json         ({len(manifest_bytes):>8,} B)  [DEFLATED]")

        # 写入 signature.p7s
        zf.writestr('signature.p7s', signature, zipfile.ZIP_STORED)
        _log(f"🔏 signature.p7s        ({len(signature):>8,} B)  [STORED]")

        # 写入时间戳 token（可选）
        if timestamp_tsr:
            zf.writestr('timestamp.tsr', timestamp_tsr, zipfile.ZIP_STORED)
            _log(f"🕒 timestamp.tsr        ({len(timestamp_tsr):>8,} B)  [STORED]")

    # 替换原文件
    os.replace(tmp_path, path)
    _log(f"\n✅ 签名完成: {path} ({os.path.getsize(path):,} B)")
    _log(f"   算法: {algo}")

    if gen_key:
        return cert_path, key_path



def verify_aidoc(path):
    """
    验证 AIDOC 文件的数字签名。

    验证流程：
    1. 验证 signature.p7s 对 manifest.json 的签名
    2. 验证 manifest.json 中所有文件的哈希是否匹配
    """
    if not os.path.exists(path):
        _die(f"文件不存在: {path}")
    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")

    openssl = _get_openssl()
    if not openssl:
        _die("找不到 openssl，无法验证签名")

    with zipfile.ZipFile(path, 'r') as zf:
        # 检查签名相关文件是否存在
        if 'manifest.json' not in [n.filename for n in zf.infolist()]:
            _die("容器中未找到 manifest.json（未签名）")
        if 'signature.p7s' not in [n.filename for n in zf.infolist()]:
            _die("容器中未找到 signature.p7s（未签名）")

        manifest_data = zf.read('manifest.json')
        sig_data = zf.read('signature.p7s')
        manifest = json.loads(manifest_data.decode('utf-8'))

    # 1. 验证 PKCS#7 签名
    import tempfile
    import subprocess

    tmp_files = []
    try:
        # 创建临时文件
        for name, data in [('manifest', manifest_data), ('sig', sig_data)]:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{name}')
            f.write(data)
            f.close()
            tmp_files.append(f.name)

        manifest_path = tmp_files[0]
        sig_path = tmp_files[1]

        # 使用 openssl 验证 PKCS#7 分离签名
        # -noverify 表示不验证证书链（只验证签名有效性）
        # 实际使用时应该提供 -CAfile 验证完整链
        result = subprocess.run([
            openssl, 'smime', '-verify',
            '-in', sig_path,
            '-content', manifest_path,
            '-inform', 'DER',
            '-noverify',
        ], capture_output=True, text=True)

        # 提取签名者证书信息
        cert_result = subprocess.run([
            openssl, 'pkcs7', '-in', sig_path,
            '-inform', 'DER', '-print_certs',
            '-noout', '-text',
        ], capture_output=True, text=True)

    finally:
        for f in tmp_files:
            if os.path.exists(f):
                os.unlink(f)

    # 2. 验证文件哈希
    hashes_match = True
    with zipfile.ZipFile(path, 'r') as zf:
        for filename, expected in manifest.get('files', {}).items():
            if filename == 'manifest.json' or filename == 'signature.p7s':
                continue
            try:
                data = zf.read(filename)
                actual_hash = _compute_sha256(data)
                if actual_hash != expected['sha256']:
                    _log(f"  ❌ {filename}: 哈希不匹配")
                    hashes_match = False
            except KeyError:
                _log(f"  ❌ {filename}: 文件缺失")
                hashes_match = False

    # 输出结果
    signature_valid = result.returncode == 0

    print()
    if signature_valid and hashes_match:
        print(f"  ✅ 签名有效 — 文件完整，未被篡改")

        # 从证书输出中提取信息
        cert_text = cert_result.stdout
        subject = _extract_cert_field(cert_text, 'Subject:')
        issuer = _extract_cert_field(cert_text, 'Issuer:')
        valid_from = _extract_cert_field(cert_text, 'Not Before:')
        valid_to = _extract_cert_field(cert_text, 'Not After :')

        print(f"    签署者: {subject or 'N/A'}")
        print(f"    颁发者: {issuer or 'N/A'}")
        print(f"    有效期: {valid_from or ''} — {valid_to or ''}")
        print(f"    算法:   {manifest.get('algorithm', 'N/A')}")
        print(f"    签署于: {manifest.get('signed_at', 'N/A')}")

        # 检查是否有时间戳
        with zipfile.ZipFile(path, 'r') as zf:
            if 'timestamp.tsr' in [n.filename for n in zf.infolist()]:
                tsr_data = zf.read('timestamp.tsr')
                import tempfile as tf
                tsr_fd2, tsr_path2 = tf.mkstemp(suffix='.tsr')
                os.write(tsr_fd2, tsr_data); os.close(tsr_fd2)
                try:
                    r2 = subprocess.run(
                        [openssl, 'ts', '-reply', '-in', tsr_path2, '-text'],
                        capture_output=True, text=True)
                    if r2.returncode == 0:
                        ts_time = _extract_cert_field(r2.stdout, 'Time stamp:')
                        if ts_time:
                            print(f"    时间戳: {ts_time}")
                finally:
                    os.unlink(tsr_path2)

        return True
    else:
        print(f"  {'❌ 签名无效!' if not signature_valid else '✅ 签名有效'}")
        print(f"  {'❌ 文件已被篡改!' if not hashes_match else '✅ 文件完整'}")
        if result.stderr:
            print(f"    原因: {result.stderr.strip()}")
        return False


def _extract_cert_field(cert_text, prefix):
    """从 openssl 证书输出中提取字段值。"""
    for line in cert_text.split('\n'):
        line = line.strip()
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _generate_self_signed_cert():
    """生成测试用的自签名证书和密钥。"""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    import datetime

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 创建自签名证书
    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, "AIDOC Test Cert"),
        x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "AIDOC"),
    ])

    cert = x509.CertificateBuilder()\
        .subject_name(subject)\
        .issuer_name(issuer)\
        .public_key(key.public_key())\
        .serial_number(1)\
        .not_valid_before(datetime.datetime.utcnow())\
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))\
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )\
        .sign(key, hashes.SHA256())

    cert_path = "/tmp/aidoc-test-cert.pem"
    key_path = "/tmp/aidoc-test-key.pem"

    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(Encoding.PEM))
    with open(key_path, 'wb') as f:
        f.write(key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption(),
        ))

    return cert_path, key_path


# ═══════════════════════════════════════════════
#  CLI Dispatch
# ═══════════════════════════════════════════════

def _log(msg):
    print(msg)


def _die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def cmd_init(args):
    output = "untitled.aidoc"
    title = "Untitled"

    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == '--title' and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        else:
            i += 1

    pack(output=output, title=title)
    _log(f"\n💡 试试: aidoc md {output}")


def cmd_create(args):
    if not args:
        _die("用法: aidoc create <文件...> [-o OUTPUT] [--title TITLE] [--author AUTHOR] [--tags TAGS]")

    doc_path = None
    md_path = None
    extra_files = []
    output = None
    title = None
    author = None
    tags = None

    file_args = []
    i = 0
    while i < len(args):
        if args[i].startswith('-'):
            if args[i] == '-o' and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            elif args[i] == '--title' and i + 1 < len(args):
                title = args[i + 1]
                i += 2
            elif args[i] == '--author' and i + 1 < len(args):
                author = args[i + 1]
                i += 2
            elif args[i] == '--tags' and i + 1 < len(args):
                tags = [t.strip() for t in args[i + 1].split(',')]
                i += 2
            else:
                i += 1
        else:
            file_args.append(args[i])
            i += 1

    # Classify files
    md_exts = {'.md', '.markdown', '.mdown'}
    doc_exts = {'.docx', '.doc', '.pdf', '.xlsx', '.xls', '.pptx', '.ppt'}

    for f in file_args:
        ext = os.path.splitext(f)[1].lower()
        if ext in md_exts and md_path is None:
            md_path = f
        elif ext in doc_exts and doc_path is None:
            doc_path = f
        else:
            extra_files.append(f)

    pack(
        doc_path=doc_path,
        md_path=md_path,
        output=output,
        title=title,
        author=author,
        tags=tags,
        extra_files=extra_files if extra_files else None,
    )


def cmd_md(path):
    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")

    # 优先使用极速模式（跳过 ZIP 中央目录）
    content = read_md_fast(path)
    if content is not None:
        print(content, end='')
        return

    # 极速模式失败时自动降级到标准模式
    content = read_md(path)
    if content is None:
        _die("容器中未找到 content.md")
    print(content, end='')


def cmd_ls(path):
    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")
    files = list_files(path)
    total_raw = 0
    total_comp = 0

    print(f"\n📦 {os.path.basename(path)}  —  {len(files)} 个文件\n")
    print(f"  {'名称':30s} {'原始大小':>10s} {'实际大小':>10s} {'方式':8s}")
    print(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*8}")
    for f in files:
        print(f"  {f['name']:30s} {f['size']:>10,} B {f['compressed']:>10,} B {f['compression']:8s}")
        total_raw += f['size']
        total_comp += f['compressed']

    ratio = f"{total_comp / total_raw * 100:.1f}%" if total_raw > 0 else "N/A"
    print(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*8}")
    print(f"  {'合计':30s} {total_raw:>10,} B {total_comp:>10,} B  压缩比: {ratio}")


def cmd_meta(path):
    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")
    meta = read_metadata(path)
    if not meta:
        _die("未找到元数据")

    print(f"\n📋 元数据:")
    for k, v in meta.items():
        if isinstance(v, list):
            print(f"    {k:15s}: {', '.join(v)}")
        elif isinstance(v, dict):
            print(f"    {k:15s}:")
            for sk, sv in v.items():
                print(f"      {sk:13s}: {sv}")
        else:
            print(f"    {k:15s}: {v}")


def cmd_info(path):
    """Alias for meta + ls combined."""
    cmd_meta(path)
    print()
    cmd_ls(path)


def cmd_check(path):
    ok = is_valid(path)
    if ok:
        meta = read_metadata(path)
        title = meta.get('title', 'unknown') if meta else 'unknown'
        print(f"✅ `{os.path.basename(path)}` — 有效 AIDOC (标题: {title})")
    else:
        _die(f"无效或非 AIDOC 文件: {path}")


def cmd_extract(args):
    if not args:
        _die("用法: aidoc extract <file.aidoc> [output_dir]")
    path = args[0]
    output_dir = args[1] if len(args) > 1 else 'extracted'

    if not is_valid(path):
        _die(f"不是有效的 .aidoc 文件: {path}")

    files = list_files(path)
    for f in files:
        out = extract_file(path, f['name'], output_dir)
        print(f"  ✅ {f['name']:30s} → {out}")
    print(f"\n📂 已提取到: {os.path.abspath(output_dir)}/")


def cmd_sign(args):
    """sign 命令"""
    if not args:
        _die("用法: aidoc sign <file.aidoc> --cert cert.pem --key key.pem [--sm2]")

    path = None
    cert_path = None
    key_path = None
    sm2 = False
    gen_key = False
    tsa_url = None

    i = 0
    file_args = []
    while i < len(args):
        if args[i].startswith('-'):
            if args[i] == '--cert' and i + 1 < len(args):
                cert_path = args[i + 1]
                i += 2
            elif args[i] == '--key' and i + 1 < len(args):
                key_path = args[i + 1]
                i += 2
            elif args[i] == '--sm2':
                sm2 = True
                i += 1
            elif args[i] == '--gen-key':
                gen_key = True
                i += 1
            elif args[i] == '--tsa' and i + 1 < len(args):
                tsa_url = args[i + 1]
                i += 2
            else:
                i += 1
        else:
            file_args.append(args[i])
            i += 1

    if file_args:
        path = file_args[0]

    if not path:
        _die("需要指定 .aidoc 文件路径")

    sign_aidoc(path, cert_path=cert_path, key_path=key_path, sm2=sm2, gen_key=gen_key, tsa_url=tsa_url)


def cmd_verify(args):
    """verify 命令"""
    if not args:
        _die("用法: aidoc verify <file.aidoc>")
    result = verify_aidoc(args[0])
    if not result:
        sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0)

    if sys.argv[1] in ('-v', '--version'):
        print(f"aidoc v{__version__}")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    handlers = {
        'init': cmd_init,
        'create': cmd_create,
        'md': lambda a: cmd_md(a[0]) if a else _die("需要 .aidoc 文件路径"),
        'ls': lambda a: cmd_ls(a[0]) if a else _die("需要 .aidoc 文件路径"),
        'meta': lambda a: cmd_meta(a[0]) if a else _die("需要 .aidoc 文件路径"),
        'info': lambda a: cmd_info(a[0]) if a else _die("需要 .aidoc 文件路径"),
        'check': lambda a: cmd_check(a[0]) if a else _die("需要 .aidoc 文件路径"),
        'extract': cmd_extract,
        'sign': cmd_sign,
        'verify': cmd_verify,
    }

    if cmd not in handlers:
        print(f"未知命令: {cmd}")
        print("试试: aidoc --help")
        sys.exit(1)

    handlers[cmd](args)


if __name__ == '__main__':
    main()
