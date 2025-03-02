from cat.rabbit_hole import RabbitHole

from cat.plugins.multicat.decorators import option, get_true_class

from cat.utils import singleton
from cat.log import log


@option(RabbitHole)
@singleton
class MyRabbitHole(get_true_class(RabbitHole)):
    def _send_progress_notification(self, cat, perc_read, file_source):
        """Helper method to send progress notification"""
        cat.send_ws_message(
            content={
                "status": "progress",
                "perc_read": perc_read,
                "source": file_source,
                "type": "doc-reading-progress",
        }, msg_type="json-notification")

    def _send_completion_notification(self, cat, file_source):
        """Helper method to send completion notification"""
        cat.send_ws_message(
            content={
                "status": "done",
                "perc_read": 100,
                "source": file_source,
                "type": "doc-reading-progress",
            }, msg_type="json-notification")

    def store_documents(self, cat, docs, source, metadata):
        time_last_notification = time.time()
        time_interval = 10  # a notification every 10 secs
        stored_points = []
        file_source = metadata.get("file_id", source)

        log.info(f"Preparing to memorize {len(docs)} vectors")
        
        # hook the docs before they are stored in the vector memory
        docs = cat.mad_hatter.execute_hook(
            "before_rabbithole_stores_documents", docs, cat=cat
        )

        for d, doc in enumerate(docs):
            perc_read = int(d / len(docs) * 100)
            
            # Send periodic text updates
            if time.time() - time_last_notification > time_interval:
                time_last_notification = time.time()
                read_message = f"Read {perc_read}% of {source}"
                cat.send_ws_message(read_message)
                log.warning(read_message)

            # Send detailed progress update
            self._send_progress_notification(cat, perc_read, file_source)

            # Process document
            doc.metadata.update({
                "source": source,
                "when": time.time()
            })
            # Add custom metadata
            for k,v in metadata.items():
                doc.metadata[k] = v

            doc = cat.mad_hatter.execute_hook(
                "before_rabbithole_insert_memory", doc, cat=cat
            )
            
            inserting_info = f"{d + 1}/{len(docs)}):    {doc.page_content}"
            if doc.page_content != "":
                doc_embedding = cat.embedder.embed_documents([doc.page_content])
                stored_point = cat.memory.vectors.declarative.add_point(
                    doc.page_content,
                    doc_embedding[0],
                    doc.metadata,
                )
                stored_points.append(stored_point)
                log.info(f"Inserted into memory ({inserting_info})")
            else:
                log.info(f"Skipped memory insertion of empty doc ({inserting_info})")

            # wait a little to avoid APIs rate limit errors
            time.sleep(0.05)

        # hook the points after they are stored in the vector memory
        cat.mad_hatter.execute_hook(
            "after_rabbithole_stored_documents", source, stored_points, cat=cat
        )

        # Send completion notifications
        finished_reading_message = f"Finished reading {source}, I made {len(docs)} thoughts on it."
        cat.send_ws_message(finished_reading_message)
        self._send_completion_notification(cat, file_source)
        log.warning(f"Done uploading {source}")