import { Route as RootRoute } from './routes/__root'
import { Route as IndexRoute } from './routes/index'
import { Route as ToolRoute } from './routes/tool'
import { Route as ToolsRoute } from './routes/tools'
import { Route as AboutRoute } from './routes/about'
import { Route as CvesRoute } from './routes/cves'
import { Route as CveDetailRoute } from './routes/cve'

export const routeTree = RootRoute.addChildren([IndexRoute, ToolsRoute, AboutRoute, ToolRoute, CveDetailRoute, CvesRoute])