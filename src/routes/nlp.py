from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schema.nlp import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers import NLPController
from models import ResponseStatus

import logging

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):
    logger.info(f"[INDEX] Starting indexing for project_id={project_id}")

    project_model = await ProjectModel.create_instance(db_client=request.app.mongodb_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.mongodb_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    if not project:
        logger.warning(f"[INDEX] Project not found: {project_id}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": ResponseStatus.PROJECT_NOT_FOUND_ERROR.value}
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
    )

    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0

    while has_records:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.id, page_no=page_no)
        if len(page_chunks):
            page_no += 1

        if not page_chunks:
            logger.info(f"[INDEX] No more chunks found. Ending pagination at page {page_no}")
            has_records = False
            break

        chunks_ids = list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            do_reset=push_request.do_reset,
            chunks_ids=chunks_ids
        )

        if not is_inserted:
            logger.error(f"[INDEX] Insertion into vector DB failed for project {project_id}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": ResponseStatus.INSERT_INTO_VECTORDB_ERROR.value}
            )

        inserted_items_count += len(page_chunks)
        logger.info(f"[INDEX] Inserted {len(page_chunks)} chunks (Total so far: {inserted_items_count})")

    logger.info(f"[INDEX] Completed indexing project: {project_id}, total inserted: {inserted_items_count}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": ResponseStatus.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    logger.info(f"[INFO] Fetching vector DB info for project_id={project_id}")

    project_model = await ProjectModel.create_instance(db_client=request.app.mongodb_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
    )

    collection_info = nlp_controller.get_vector_db_collection_info(project=project)

    logger.info(f"[INFO] Retrieved vector DB info for project_id={project_id}")
    return JSONResponse(
        content={
            "status": ResponseStatus.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    logger.info(f"[SEARCH] Searching in vector DB for project_id={project_id}")

    project_model = await ProjectModel.create_instance(db_client=request.app.mongodb_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        logger.warning(f"[SEARCH] Project not found: {project_id}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": ResponseStatus.PROJECT_NOT_FOUND_ERROR.value}
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
    )

    search_results = nlp_controller.search_vector_db_collection(
        project=project,
        query=search_request.query_text,
        limit=search_request.limit
    )

    if not search_results:
        logger.info(f"[SEARCH] No results found for query: {search_request.query_text}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": ResponseStatus.VECTORDB_SEARCH_ERROR.value}
        )

    logger.info(f"[SEARCH] Found {len(search_results)} results for query: {search_request.query_text}")
    return JSONResponse(
        content={
            "status": ResponseStatus.VECTORDB_SEARCH_SUCCESS.value,
            "results": search_results
        }
    )
