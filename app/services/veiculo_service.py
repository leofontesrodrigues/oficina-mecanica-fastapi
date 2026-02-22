from sqlalchemy.orm import Session
from app.models.veiculo import Veiculo
from app.repositories.veiculo_repo import VeiculoRepository
from app.schemas.veiculo_schema import VeiculoCreate

class VeiculoService:

    @staticmethod
    def criar_veiculo(db: Session, veiculo_data: VeiculoCreate):
        # valida placa duplicada
        if VeiculoRepository.get_by_placa(db, veiculo_data.placa):
            return None

        veiculo = Veiculo(**veiculo_data.dict())
        return VeiculoRepository.create(db, veiculo)

    @staticmethod
    def listar_veiculos(db: Session):
        return VeiculoRepository.get_all(db)

    @staticmethod
    def listar_por_cliente(db: Session, cliente_id: int):
        return VeiculoRepository.get_by_cliente(db, cliente_id)

    @staticmethod
    def editar_veiculo(db, veiculo_id, veiculo_data):
        veiculo = VeiculoRepository.get_by_id(db, veiculo_id)

        if not veiculo:
            return None

        # atualiza campos
        veiculo.placa = veiculo_data.placa
        veiculo.marca = veiculo_data.marca
        veiculo.modelo = veiculo_data.modelo
        veiculo.ano = veiculo_data.ano
        veiculo.cor = veiculo_data.cor

        return VeiculoRepository.update(db, veiculo)

    @staticmethod
    def excluir_veiculo(db: Session, veiculo_id: int):
        veiculo = VeiculoRepository.get_by_id(db, veiculo_id)
        if not veiculo:
            return None

        VeiculoRepository.delete(db, veiculo)
        return True
