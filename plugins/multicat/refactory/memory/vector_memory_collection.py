from cat.memory.vector_memory_collection import VectorMemoryCollection

from cat.plugins.multicat.decorators import option, get_true_class


@option(VectorMemoryCollection)
class MyVectorMemoryCollection(VectorMemoryCollection):
    def update_points_by_metadata(self, points_ids=[], metadata={}):
        """
        Aggiorna i metadati dei punti specificati nella collezione vettoriale.
        
        Args:
            points_ids (list): Lista degli ID dei punti da aggiornare
            metadata (dict): Dizionario contenente i metadati da applicare
            
        Returns:
            dict: Risultato dell'operazione di aggiornamento
        """
        # Aggiorna i metadati dei punti attraverso il client
        update_result = self.client.set_payload(
            collection_name=self.collection_name,
            points=points_ids,
            payload=metadata,
        )
        return update_result