from app.database.database import DB
from app.engine.records import records
from app.engine import save

save_fn = sys.argv[1]
save_fp = save.load(save_fn)
record_data = save_fp['record_book']
record_book = records.load(record_data)

