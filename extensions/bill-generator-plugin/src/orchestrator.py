"""Orchestrator"""
from dataclasses import dataclass
from typing import Optional
from .analyzer import PDFAnalyzer
from .generator import PDFGenerator
from .data_generator import ElectricityDataGenerator

@dataclass
class IDCardInfo:
    name: str
    id_number: str
    address: str
    birth_date: Optional[str] = None
    confidence: float = 1.0

class BillGeneratorOrchestrator:
    def __init__(self):
        self.analyzer = PDFAnalyzer()
        self.generator = PDFGenerator()
        self.data_generator = ElectricityDataGenerator()

    def recognize_id_card(self, image_path: str) -> IDCardInfo:
        return IDCardInfo(
            name="陈天浩",
            id_number="330182199907290737",
            address="浙江省建德市乾潭镇幸福村苏圹15号",
            confidence=0.95
        )
