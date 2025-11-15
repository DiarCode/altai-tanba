-- CreateEnum
CREATE TYPE "DocumentAnalysisStatus" AS ENUM ('PROCESSING', 'COMPLETED', 'FAILED');

-- CreateTable
CREATE TABLE "document_analyses" (
    "id" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "status" "DocumentAnalysisStatus" NOT NULL DEFAULT 'PROCESSING',
    "fraudSentences" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "mistakeWords" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "documentType" TEXT,
    "errorLog" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "document_analyses_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "document_analyses_documentId_key" ON "document_analyses"("documentId");
