from cat.memory.vector_memory_collection import VectorMemoryCollection

from cat.plugins.multicat.decorators import option
from qdrant_client import models

from cat.log import log


@option(VectorMemoryCollection)
class MyVectorMemoryCollection(VectorMemoryCollection):
    def update_points_by_metadata(self, points_ids=[], metadata={}):
        """
        Updates the metadata of specified points in the vector collection.
        
        Args:
            points_ids (list): List of point IDs to update
            metadata (dict): Dictionary containing the metadata to apply
            
        Returns:
            dict: Result of the update operation
        """
        # Update the metadata of points through the client
        update_result = self.client.set_payload(
            collection_name=self.collection_name,
            points=points_ids,
            payload=metadata,
        )
        return update_result

    def _filter_exclude_file_ids(self, ids, chat_id=None):
        return models.Filter(
            must_not=[
                models.FieldCondition(key="metadata.file_id", match=models.MatchAny(any=ids))
            ],
            must=[
                *self._build_condition("chats_id", [chat_id])
            ] if chat_id else None
        )

    def get_all_file_names(self, chat_id=None):
        """
        Returns the list of all file names present in the collection.
        
        Returns:
            list: List of file names
        """

        # a list of Dict
        #  dict: {
        #     "id": str,
        #     "name": str
        # }

        all_vectors = []
        next_offset = None

        ids = set()

        # cycle while not exist more vector with file_id in ids
        while True:
            vectors, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=self._filter_exclude_file_ids(ids, chat_id),
                limit=1,
                offset=next_offset,
                with_vectors=False,
                with_payload=True,
            )

            if len(vectors) == 0:
                break

            metadata = vectors[0].payload["metadata"]

            file_id = metadata.get("file_id", "")
            name = metadata.get("source", "")

            all_vectors.append(
                {
                    "name": name,
                    "file_id": file_id
                }
            )

            ids.add(file_id)


        # Print results
        log.debug(f"results: {all_vectors}")

        return all_vectors