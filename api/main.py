
from fastapi import FastAPI, Query, HTTPException
from services.datafone_service import buscar_membros_por_area

app = FastAPI(title="PGD1 API", version="1.0")


@app.get("/membros")
def membros(area: str = Query(..., description="Sigla da área, ex: DVGD")):
    try:
        dados = buscar_membros_por_area(area)
        return dados
    except ValueError as e:
        # erros de validação (ex: área vazia, URL não setada)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # erro inesperado (selenium, site fora, etc)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar membros: {e}")
