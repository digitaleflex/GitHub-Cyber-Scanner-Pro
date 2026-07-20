import { Route as RootRoute } from './routes/__root'
import { Route as IndexRoute } from './routes/index'
import { Route as NewsRoute } from './routes/news'
import { Route as IncidentsRoute } from './routes/incidents'
import { Route as ReportsRoute } from './routes/reports'
import { Route as CvesRoute } from './routes/cves'
import { Route as KeywordsRoute } from './routes/keywords'

export const routeTree = RootRoute.addChildren([IndexRoute, NewsRoute, IncidentsRoute, ReportsRoute, CvesRoute, KeywordsRoute])
