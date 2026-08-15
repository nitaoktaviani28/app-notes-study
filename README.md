# complite study

Aplikasi web untuk manajemen kuliah:
- Jadwal kuliah + kalender
- Alert pengingat ke Telegram
- Penyimpanan materi (PDF/PPT) per folder matkul
- Baca materi di web
- AI Summary + AI Quiz generator (Amazon Bedrock Nova)
- Nilai tracker per semester
- Pomodoro timer
- Daily routine notes + alert Telegram

## 1) Setup Lokal

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app/seed.py
uvicorn app.main:app --reload
```

Buka: http://localhost:8000

## 2) Konfigurasi Telegram

1. Buat bot dengan `@BotFather`
2. Ambil bot token dan isi `TELEGRAM_BOT_TOKEN`
3. Dapatkan `CHAT_ID` kamu lalu isi `TELEGRAM_CHAT_ID`

## 3) Konfigurasi Bedrock Nova

Isi kredensial AWS dan BEDROCK_MODEL_ID di .env.
Model default: amazon.nova-lite-v1:0.

Contoh konfigurasi minimum:

AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

Catatan IAM:
- Beri izin bedrock:InvokeModel ke model Nova yang dipakai.

## 4) Penyimpanan File Materi

Mode local (default):
- STORAGE_BACKEND=local
- File tersimpan di folder storage/ pada server aplikasi.

Mode S3:
- STORAGE_BACKEND=s3
- Isi S3_BUCKET, S3_REGION, S3_PREFIX
- File diupload ke s3://<bucket>/<prefix>/<folder_matkul>/<uuid>.pdf atau .pptx
- Tombol Buka di UI menggunakan presigned URL otomatis.

Contoh:

STORAGE_BACKEND=s3
S3_BUCKET=s3-study-complete
S3_REGION=ap-southeast-1
S3_PREFIX=complite-study/materials

## 5) IAM Role EC2 (Recommended)

File policy siap pakai ada di folder aws/:
- aws/iam-policy-complite-study.json
- aws/trust-policy-ec2.json

Contoh langkah via AWS CLI:

1. Create role:
aws iam create-role --role-name CompliteStudyEc2Role --assume-role-policy-document file://aws/trust-policy-ec2.json

2. Attach policy app:
aws iam put-role-policy --role-name CompliteStudyEc2Role --policy-name CompliteStudyInlinePolicy --policy-document file://aws/iam-policy-complite-study.json

3. Create instance profile:
aws iam create-instance-profile --instance-profile-name CompliteStudyEc2Profile

4. Add role ke instance profile:
aws iam add-role-to-instance-profile --instance-profile-name CompliteStudyEc2Profile --role-name CompliteStudyEc2Role

5. Attach instance profile ke EC2 instance yang menjalankan Docker.

Jika pakai IAM role, tidak perlu isi AWS_ACCESS_KEY_ID dan AWS_SECRET_ACCESS_KEY di .env.

## 6) Deploy Docker di EC2

```bash
docker compose up -d --build
```

## 7) CI/CD GitHub Actions -> Docker Hub

Workflow file:
- .github/workflows/docker-ci-cd.yml

Image target:
- haechanlovelove/complite-study

Tambahkan GitHub repository secrets:
- DOCKERHUB_USERNAME: username Docker Hub
- DOCKERHUB_TOKEN: Docker Hub Access Token

Trigger build:
- push ke branch main
- atau manual via workflow_dispatch

Tag hasil push:
- latest (di default branch)
- main
- sha-<commit>

## 8) Jalankan di EC2 dari image Docker Hub

Contoh command di EC2:

```bash
cat > .env << 'EOF'
APP_NAME=complite-study
APP_ENV=prod
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=change-this-to-a-long-random-secret
DATABASE_URL=sqlite:///./data/complite_study.db

STORAGE_BACKEND=s3
S3_BUCKET=s3-study-complete
S3_REGION=ap-southeast-1
S3_PREFIX=complite-study/materials

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

AWS_REGION=ap-southeast-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
EOF

docker pull haechanlovelove/complite-study:latest

docker rm -f complite-study || true
docker run -d --name complite-study \
	--restart unless-stopped \
	--env-file .env \
	-p 8000:8000 \
	haechanlovelove/complite-study:latest
```

Aplikasi listen di port `8000` (sesuaikan Security Group EC2).

## Struktur

- `app/` backend FastAPI + scheduler + AI service
- `templates/` halaman web
- `static/` css/js
- `storage/` file materi upload
- `data/` sqlite db
