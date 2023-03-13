try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.engine import records

save_fn = sys.argv[1]
with open(save_fn, 'rb') as fp:
    s_dict = pickle.load(fp)
record_book = records.Recordkeeper.restore(s_dict['records'])

levels = record_book.get_levels()
print(levels)
turncounts = record_book.get_turncounts(levels)
for l, t in zip(levels, turncounts):
    print("%s: %s" % (l, t))

print("\n*** Deaths ***")
for kill_record in record_book.death:
    print("%s killed %s in level %s on turn %s" % (kill_record.killer, kill_record.killee, kill_record.level_nid, kill_record.turn))

print("\n*** Levels ***")
for level_nid in levels:
    print("* %s *" % level_nid)
    level_dict = {}
    for level_record in record_book.levels:
        if level_record.level_nid == level_nid:
            level_dict[level_record.unit_nid] = max(level_dict.get(level_record.unit_nid, 0), level_record.num)
    for unit_nid, num in level_dict.items():
        print("%s: %s" % (unit, num))

print("\n *** Money ***")
for level_nid in levels:
    print("* %s *" % level_nid)
    valid_records = [record for record in record_book.money if record.level_nid == level_nid]
    valid_records = sorted(valid_records, key=lambda x: x.turn)
    for record in valid_records:
        print("%s: %d" % (record.turn, record.num))
