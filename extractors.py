"""Feature extractors for whether a query matches with an entity.

When defining a new query, use @Extractor to register it into the extractor
database.
"""
import entitydb

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
    summary = entitydb.LookupEntitySummary(entity)
    return [(q_type + 'NSumCharOverlap', len(set(query).intersection(set(summary))))]
  except IndexError:
    return [(q_type + 'NO_SUMMARY', 1)]


@Extractor("sumchar")
def ExtractSumCharOverlapFeature((q_type, query), entity):
  try:
    summary = entitydb.LookupEntitySummary(entity)
    return [(q_type + 'SumCharOverlap=%s' % i, 1) for i in set(query).intersection(set(summary))]
  except IndexError:
    return [(q_type + 'NO_SUMMARY', 1)]


@Extractor("cont_match")
def ExtractQueryInContent((q_type, query), entity):
  result = []
  try:
    content = entitydb.LookupEntityContent(entity)
    if query in content:
      result.append((q_type + "SHOWED_UP_IN_CONTENT", 1))
    content_charset = set(content)
    for char in set(query).intersection(content_charset):
      result.append((q_type + "ContCharOverlap=%s" % char, 1))

    return result

  except IndexError:
    return [(q_type + 'NO_CONTENT', 1)]


def EnumerateNGram(s, n):
  l = len(s)
  result = []
  for i in range(l - n + 1):
    result.append(s[i:i+n])
  return result


# Bigram features

@Extractor("cont_bigram")
def ExtractQueryInContentBigram((q_type, query), entity):
  result = []
  try:
    content = entitydb.LookupEntityContent(entity)
    content_charset = set(EnumerateNGram(content, 2))
    overlaps = len(set(EnumerateNGram(query, 2)).intersection(content_charset))
    result.append((q_type + "ContBigramOverlaps", overlaps))

    return result

  except IndexError:
    return [(q_type + 'NO_CONTENT', 1)]


@Extractor("cont_trigram")
def ExtractQueryInContentTrigram((q_type, query), entity):
  result = []
  try:
    content = entitydb.LookupEntityContent(entity)
    content_charset = set(EnumerateNGram(content, 3))
    overlaps = len(set(EnumerateNGram(query, 3)).intersection(content_charset))
    result.append((q_type + "ContTrigramOverlaps", overlaps))

    return result

  except IndexError:
    return [(q_type + 'NO_CONTENT', 1)]


def Extract2gramOverlap(text_ent_name, text_extractor):
  def wrappee((q_type, query), entity):
    result = []
    try:
      content = text_extractor(entity)
      content_charset = set(EnumerateNGram(content, 2))
      overlaps = len(set(EnumerateNGram(query, 2)).intersection(content_charset))
      result.append((q_type + text_ent_name + "BigramOverlaps", overlaps))

      return result

    except IndexError:
      return [(q_type + 'NO_%s' % text_ent_name, 1)]

  return wrappee

Extractor("2gcont")(Extract2gramOverlap(
  'CONTENT', lambda entity: entitydb.LookupEntityContent(entity)))
Extractor("2gsum")(Extract2gramOverlap(
  'SUMMARY', lambda entity: entitydb.LookupEntitySummary(entity)))
Extractor("2gsurf")(Extract2gramOverlap('ENTITY', lambda entity: entity))


def CombinedModel(*models):
  def wrappee(*args, **kw):
    result = []
    for model in models:
      result.extend(model(*args, **kw))
    return result
  return wrappee


def BuildExtractor(extractor_name):
  name_list = extractor_name.split(',')
  return CombinedModel(*[_extractors_map[name] for name in name_list])
