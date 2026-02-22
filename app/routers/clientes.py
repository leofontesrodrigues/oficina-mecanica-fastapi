from fastapi import APIRouter, Depends, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from urllib.parse import quote
import re
from app.core.dependencies import get_db
from app.core.uploads import remove_uploaded_file, save_image_upload
from app.services.cliente_service import ClienteService
from app.schemas.cliente_schema import ClienteCreate

router = APIRouter(prefix="/clientes", tags=["Clientes"])
templates = Jinja2Templates(directory="app/templates")

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    if digito1 == 10:
        digito1 = 0

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    if digito2 == 10:
        digito2 = 0

    return cpf[-2:] == f"{digito1}{digito2}"


def validar_cep(cep: str) -> bool:
    cep = re.sub(r"\D", "", cep or "")
    return len(cep) == 8

@router.get("/", response_class=HTMLResponse)
def listar_clientes(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):

    per_page = 10

    clientes, total = ClienteService.listar_clientes(
        db,
        search=search,
        page=page,
        per_page=per_page
    )

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "clientes/clientes.html",
        {
            "request": request,
            "clientes": clientes,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        }
    )

@router.post("/novo")
def criar_cliente(
    nome: str = Form(None),  # 🔥 mudança AQUI
    cpf_cnpj: str = Form(None),
    cep: str = Form(None),
    bairro: str = Form(None),
    cidade: str = Form(None),
    uf: str = Form(None),
    telefone: str = Form(None),
    email: str = Form(None),
    endereco: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    if telefone:
        telefone = re.sub(r"\D", "", telefone)

    cpf_cnpj = re.sub(r"\D", "", cpf_cnpj or "")
    cep = re.sub(r"\D", "", cep or "")
    uf = (uf or "").strip().upper()

    if not validar_cpf(cpf_cnpj):
        msg = quote("CPF inválido")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    if not validar_cep(cep):
        msg = quote("CEP inválido (informe 8 dígitos)")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )
    
    if email:
        if not re.match(EMAIL_REGEX, email):
            msg = quote("E-mail inválido")
            return RedirectResponse(
                url=f"/clientes?error={msg}",
                status_code=303
            )
    # ✅ validação manual (agora funciona!)
    if not nome or len(nome.strip()) < 3:
        msg = quote("O nome do cliente é obrigatório (mínimo 3 caracteres)")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    existente = ClienteService.buscar_por_cpf_cnpj(db, cpf_cnpj)
    if existente:
        msg = quote("CPF já cadastrado para outro cliente")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    try:
        foto_path = save_image_upload(foto, prefix="cliente") if foto and foto.filename else None

        cliente_data = ClienteCreate(
            nome=nome.strip(),
            cpf_cnpj=cpf_cnpj,
            cep=cep,
            bairro=(bairro or "").strip() or None,
            cidade=(cidade or "").strip() or None,
            uf=uf or None,
            telefone=telefone,
            email=email,
            endereco=(endereco or "").strip() or None,
            foto_path=foto_path,
        )

        ClienteService.criar_cliente(db, cliente_data)

        msg = quote("Cliente cadastrado com sucesso")
        return RedirectResponse(
            url=f"/clientes?success={msg}", status_code=303
        )

    except Exception as e:
        msg = quote(str(e) if str(e) else "Erro ao cadastrar cliente")
        return RedirectResponse(
            url=f"/clientes?error={msg}", status_code=303
        )

@router.post("/editar/{cliente_id}")
def editar_cliente(
    cliente_id: int,
    nome: str = Form(None),  # 🔥 importante
    cpf_cnpj: str = Form(None),
    cep: str = Form(None),
    bairro: str = Form(None),
    cidade: str = Form(None),
    uf: str = Form(None),
    telefone: str = Form(None),
    email: str = Form(None),
    endereco: str = Form(None),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if telefone:
        telefone = re.sub(r"\D", "", telefone)

    cpf_cnpj = re.sub(r"\D", "", cpf_cnpj or "")
    cep = re.sub(r"\D", "", cep or "")
    uf = (uf or "").strip().upper()

    if not validar_cpf(cpf_cnpj):
        msg = quote("CPF inválido")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    if not validar_cep(cep):
        msg = quote("CEP inválido (informe 8 dígitos)")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )
        
    if email:
        if not re.match(EMAIL_REGEX, email):
            msg = quote("E-mail inválido")
            return RedirectResponse(
                url=f"/clientes?error={msg}",
                status_code=303
            )

    # ✅ validação manual
    if not nome or len(nome.strip()) < 3:
        msg = quote("O nome do cliente é obrigatório (mínimo 3 caracteres)")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    existente = ClienteService.buscar_por_cpf_cnpj(db, cpf_cnpj)
    if existente and existente.id != cliente_id:
        msg = quote("CPF já cadastrado para outro cliente")
        return RedirectResponse(
            url=f"/clientes?error={msg}",
            status_code=303
        )

    cliente_existente = ClienteService.buscar_por_id(db, cliente_id)
    if not cliente_existente:
        msg = quote("Cliente não encontrado")
        return RedirectResponse(
            f"/clientes?error={msg}", status_code=303
        )

    try:
        foto_path = cliente_existente.foto_path
        if foto and foto.filename:
            nova_foto = save_image_upload(foto, prefix="cliente")
            remove_uploaded_file(cliente_existente.foto_path)
            foto_path = nova_foto

        cliente_data = ClienteCreate(
            nome=nome.strip(),
            cpf_cnpj=cpf_cnpj,
            cep=cep,
            bairro=(bairro or "").strip() or None,
            cidade=(cidade or "").strip() or None,
            uf=uf or None,
            telefone=telefone,
            email=email,
            endereco=(endereco or "").strip() or None,
            foto_path=foto_path,
        )

        resultado = ClienteService.editar_cliente(db, cliente_id, cliente_data)

        if not resultado:
            msg = quote("Cliente não encontrado")
            return RedirectResponse(
                f"/clientes?error={msg}", status_code=303
            )

        msg = quote("Cliente atualizado com sucesso")
        return RedirectResponse(
            f"/clientes?success={msg}", status_code=303
        )
    except Exception as e:
        msg = quote(str(e) if str(e) else "Erro ao atualizar cliente")
        return RedirectResponse(
            f"/clientes?error={msg}", status_code=303
        )

@router.post("/excluir/{cliente_id}")
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = ClienteService.buscar_por_id(db, cliente_id)
    resultado = ClienteService.excluir_cliente(db, cliente_id)

    if not resultado:
        msg = quote("Cliente não encontrado")
        
        return RedirectResponse(f"/clientes?error={msg}", status_code=303)

    if cliente:
        remove_uploaded_file(cliente.foto_path)

    msg = quote("Cliente excluído com sucesso")
    return RedirectResponse(f"/clientes?success={msg}", status_code=303)
