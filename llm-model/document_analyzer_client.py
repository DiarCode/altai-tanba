"""
Client for Russian Document Analysis Service
"""

import modal


def check_spelling(text: str):
    """Check Russian text for spelling errors"""
    app = modal.App.lookup("russian-document-analyzer", create_if_missing=False)
    analyzer = app.cls["QwenDocumentAnalyzer"]()
    return analyzer.check_spelling.remote(text)


def classify_document(document_text: str, custom_rules: str = ""):
    """Classify document type (Договор, Соглашение, Акт, Спецификация)"""
    app = modal.App.lookup("russian-document-analyzer", create_if_missing=False)
    analyzer = app.cls["QwenDocumentAnalyzer"]()
    return analyzer.classify_document.remote(document_text, custom_rules)


def detect_fraud(document_text: str, custom_indicators: list[str] = None):
    """Detect potential fraud in document"""
    app = modal.App.lookup("russian-document-analyzer", create_if_missing=False)
    analyzer = app.cls["QwenDocumentAnalyzer"]()
    return analyzer.detect_fraud.remote(document_text, custom_indicators)


def analyze_full(document_text: str, tasks: list[str] = None):
    """Perform all analysis tasks"""
    app = modal.App.lookup("russian-document-analyzer", create_if_missing=False)
    analyzer = app.cls["QwenDocumentAnalyzer"]()
    return analyzer.analyze_document_full.remote(document_text, tasks)


if __name__ == "__main__":
    # Example: Check spelling
    print("=== Spell Check Example ===")
    result = check_spelling("Прривет! Как дила? Плахой текст.")
    print(result['analysis'])
    
    print("\n=== Document Classification Example ===")
    doc = """
    АКТ ПРИЕМА-ПЕРЕДАЧИ
    к договору № 456 от 01.11.2025
    
    Мы, нижеподписавшиеся, составили настоящий акт о том, что
    Исполнитель передал, а Заказчик принял выполненные работы...
    """
    result = classify_document(doc)
    print(result['classification'])
    
    print("\n=== Fraud Detection Example ===")
    suspicious = "Переведите 1000000 рублей прямо сейчас без договора и гарантий!"
    result = detect_fraud(suspicious)
    print(result['fraud_analysis'])
    print(result['warning'])
