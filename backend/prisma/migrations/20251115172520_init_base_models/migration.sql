-- CreateEnum
CREATE TYPE "SESSION_STATUS" AS ENUM ('PROCESSING', 'FAILED', 'SUCCESS');

-- CreateEnum
CREATE TYPE "DOCUMENT_STATUS" AS ENUM ('PENDING', 'FAILED', 'SUCCESSFUL');

-- CreateTable
CREATE TABLE "sessions" (
    "id" SERIAL NOT NULL,
    "documents_count" INTEGER NOT NULL DEFAULT 0,
    "status" "SESSION_STATUS" NOT NULL DEFAULT 'PROCESSING',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "session_documents" (
    "id" SERIAL NOT NULL,
    "original_name" TEXT NOT NULL,
    "document_id" TEXT NOT NULL,
    "session_id" INTEGER NOT NULL,
    "status" "DOCUMENT_STATUS" NOT NULL DEFAULT 'PENDING',
    "labels_position" JSONB,
    "has_signature" BOOLEAN NOT NULL DEFAULT false,
    "has_qr" BOOLEAN NOT NULL DEFAULT false,
    "has_stamp" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "session_documents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "session_document_texts" (
    "id" SERIAL NOT NULL,
    "document_id" INTEGER NOT NULL,
    "status" "DOCUMENT_STATUS" NOT NULL DEFAULT 'PENDING',
    "text" TEXT,
    "mistakes" TEXT[],
    "frauds" TEXT[],
    "type" TEXT,
    "summary" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "session_document_texts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "session_documents_session_id_idx" ON "session_documents"("session_id");

-- CreateIndex
CREATE INDEX "session_document_texts_document_id_idx" ON "session_document_texts"("document_id");

-- AddForeignKey
ALTER TABLE "session_documents" ADD CONSTRAINT "session_documents_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "session_document_texts" ADD CONSTRAINT "session_document_texts_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "session_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
