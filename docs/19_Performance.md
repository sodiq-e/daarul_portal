# 19. Performance Analysis

## Observations
The project is functional but some views perform multiple ORM queries and aggregate operations directly in the request path.

## Performance Hotspots
- Report-card and results pages aggregate multiple result sets and often issue several queryset operations in one view
- Student and invoice lists may benefit from select_related and prefetch_related where relationships are used in templates
- Some views create manual loops over querysets to build context values

## Improvement Opportunities
- Use select_related/prefetch_related for frequently nested relationships
- Cache repeated settings and school configuration data
- Reduce N+1 query patterns for list pages
- Use queryset annotations where suitable for aggregate views

## Current Strengths
- The system uses reasonable filtering and grouping in the ORM
- Querysets are often scoped carefully to reduce unnecessary data loads
