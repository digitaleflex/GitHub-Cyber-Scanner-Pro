import { Route as RootRoute } from './routes/__root'
import { Route as IndexRoute } from './routes/index'
import { Route as ReportsRoute } from './routes/reports'
import { Route as CvesRoute } from './routes/cves'
import { Route as KeywordsRoute } from './routes/keywords'
import { Route as GraphRoute } from './routes/graph'
import { Route as SearchRoute } from './routes/search'

export const routeTree = RootRoute.addChildren([IndexRoute, SearchRoute, ReportsRoute, CvesRoute, KeywordsRoute, GraphRoute])
