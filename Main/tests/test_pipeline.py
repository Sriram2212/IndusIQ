from backend.pipeline.processing_pipeline import ProcessingPipeline

pipeline = ProcessingPipeline()

pipeline.process(
    "sample_data/uploads/sample.pdf"
)