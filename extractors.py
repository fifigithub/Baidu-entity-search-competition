"""Feature extractors for whether a query matches with an entity.

When defining a new query, use @Extractor to register it into the extractor
database.
"""

_extractors_map = {}

def Extractor(name):
  def wrappee(func):
    _extractors_map[name] = func
    return func
  return wrappee

@Extractor("nchar")
def ExtractNCharOverlapFeature((q_type, query), entity):
  return [(q_type + 'NCharOverlap', len(set(query).intersection(set(entity))))]


@Extractor("char")
def ExtractCharOverlapFeature((q_type, query), entity):
  return [(q_type + 'CharOverlap=%s' % i, 1) for i in set(query).intersection(set(entity))]


@Extractor("nsumchar")
def ExtractNSumCharOverlapFeature((q_type, query), entity):
  try:
    summary = entity_summary_map[entity]
    return [(q_type + 'NSumCharOverlap', len(set(query).intersection(set(summary))))]
  except:
    return [(q_type + 'NO_SUMMARY', 1)]


@Extractor("sumchar")
def ExtractSumCharOverlapFeature((q_type, query), entity):
  try:
    summary = entity_summary_map[entity]
    return [(q_type + 'SumCharOverlap=%s' % i, 1) for i in set(query).intersection(set(summary))]
  except:
    return [(q_type + 'NO_SUMMARY', 1)]


def CombinedModel(*models):
  def wrappee(*args, **kw):
    result = []
    for model in models:
      result.extend(model(*args, **kw))
    return result
  return wrappee


def BuildExtractor(name_list):
  return CombinedModel(*[_extractors_map[name] for name in name_list])
