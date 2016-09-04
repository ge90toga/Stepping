import java.util.*;
import java.io.*;
import java.net.*;

/**
 * UNSW COMP9414 assignment3
 * @Author Li Quan z5044754 & Jingmin Li z5077274
 * Group Number: 102
 *
 * Description of program:
 *
 * (1) Map storage:
 *     The program uses North, East, West, South direction mark to help agent figure out the direction it is pointing to.
 *     The agent is considered facing North with a position (0,0) at the start of the game. In order for the agent
 *     to solve path search problem and move, this program uses Java's HashMap as the way to store the map since
 *     it is fairly easy to retrive and insert. When agent is moving inside the world, it would update its map
 *     by observing the 5*5 window and store new position into map.
 *
 * (2) Resource collection phase:
 *
 *     The agent at the very beginning will start collect any "free" resource, namely, resources does not require spending
 *     stepping stone. While collecting stone, agent also get a chance to observe positions that is not included in previous map.
 *     The trigger of termination this phase is that the agent finds nothing to collect in the map which is possibly caused by two reasons:
 *     (1) resources in the current map has been all collected OR (2) Some resources are not reachable because there is no path to them.
 *     Then it go into Map exploration(expansion) phase.
 *
 *(3) Map Exploration Expansion:
 *
 *    The agent at this phase would try to expand the map it currently holds. The agent first scan through the whole map,
 *    finding positions that has never been visited. Then sort those positions by the proximity to the current position using heap sort.
 *    In this way, agent can first visit far positions first, reducing the repetition of deliberately visit near positions.
 *    Once agents finishing visit a position, it mark this position in a HashSet so that it will not try to visit this position next time.
 *
 *(4) Search strategy:
 *    Whenever the agent is trying to visit a particular position, it will invoke search function.
 *    Generally, the search algorithm used in this program is A* Search where the heuristic is the shortest move to a position computed
 *    by |x1-x0|+|y1-y0| and the g(n) is the move that has already been made.
 *
 *    The search method uses a priority queue which maintains its priority by evaluation functionf(n) = g(n)+h(n).
 *    Each state has its own value such as position, hasKey, hasAxe, number of stone...
 *    Then each state would have 4 possible next state North East South West.
 *
 *    The program will check the eligibility of each state by checking whether if it is repeated using a HashSet
 *    and whether if it is walkable by checking the object on the next position. Note that the eligibility
 *    depends on the previous state's resource status. For example, if the next position is '-' and the previous state has key, then
 *    it is fine to expand, otherwise it is not.
 *
 *(6) Gold search or collection phase
 *    The agent would eventually find gold's position. At this stage, the agent may or
 *    may not be able to move to that gold position. If it cannot, the agent would still alternates between
 *    resource collection and map expansion in order to find helpful tool or way to get to the gold position. Finally, the agent
 *    can find a path to gold once it has needed resources and walkable way. Then it goes home by searching a path to the original
 *    position (0,0)

 */
public class Agent {

    static int last_mapsize = 0;

    public char get_action(char view[][]) {

        // REPLACE THIS CODE WITH AI TO CHOOSE ACTION


        int ch = 0;

        System.out.print("Enter Action(s): ");

        try {
            while (ch != -1) {
                // read character from keyboard
                ch = System.in.read();

                switch (ch) { // if character is a valid action, return it
                    case 'F':
                    case 'L':
                    case 'R':
                    case 'C':
                    case 'U':
                    case 'f':
                    case 'l':
                    case 'r':
                    case 'c':
                    case 'u':
                        return ((char) ch);
                }
            }
        } catch (IOException e) {
            System.out.println("IO error:" + e);
        }

        return 0;
    }

    void print_view(char view[][]) {
        int i, j;

        System.out.println("\n+-----+");
        for (i = 0; i < 5; i++) {
            System.out.print("|");
            for (j = 0; j < 5; j++) {
                if ((i == 2) && (j == 2)) {
                    System.out.print('^');
                } else {
                    System.out.print(view[i][j]);
                }
            }
            System.out.println("|");
        }
        System.out.println("+-----+");
    }

    public static void main(String[] args) {


        InputStream in = null;
        OutputStream out = null;
        Socket socket = null;
        char view[][] = new char[5][5];
        char action = 'F';
        int port;

        List<Position> movePositionTasks = new ArrayList<>();
        boolean brainInitialized = false;
        Brain brain = null;
        SearchState goldPath = null;

        String state = "collect";
        ArrayList<Position> expandTargets = new ArrayList<>();
        ArrayList<Position> collectTargets = new ArrayList<>();

        Set<String> tmpUnreachableResources = new HashSet<>(); // store unreachable resources for speeding up search.

        if (args.length < 2) {
            System.out.println("Usage: java Agent -p <port>\n");
            System.exit(-1);
        }

        port = Integer.parseInt(args[1]);
        //port = 31415;
        try { // open socket to Game Engine
            socket = new Socket("localhost", port);
            in = socket.getInputStream();
            out = socket.getOutputStream();
        } catch (IOException e) {
            System.out.println("Could not bind to port: " + port);
            System.exit(-1);
        }

        try {
            while (true) {

                if(action!='n'){
                    scanView(in, view); // update surronding environment to map
                }

                if (brainInitialized && action!='n') {
                    brain.worldAction(action, view);
                }

                if (!brainInitialized) {
                    brain = new Brain(view);
                    brainInitialized = true;
                }

                //if gold is in sight, each time the move sequence finished, try searching a path to gold
                if(brain.goldPosition != null && !brain.goldOnHand&&(last_mapsize<brain.map.size())){
                    goldPath = brain.search(brain.position.x,brain.position.y,brain.goldPosition.x,brain.goldPosition.y,true);
                    if(goldPath!=null){
                        movePositionTasks = goldPath.historyPosition;
                        movePositionTasks.remove(0);
                    }
                }

                //if gold is on hand, compute a path back to home
                if(brain.goldOnHand && movePositionTasks.size()==0){//go home
                    SearchState goHomePath = brain.search(brain.position.x,brain.position.y,0,0,false);
                    movePositionTasks = goHomePath.historyPosition;
                    movePositionTasks.remove(0);
                }

                // the initial state is seaching for any collectable resources
                state = getCollectTargets(movePositionTasks, brain, goldPath, state, expandTargets, collectTargets,tmpUnreachableResources);
                // if the current collect state has nothing to collect and no gold to grab, change to expansion
                if ((state == "collect")&& collectTargets.size()==0 && movePositionTasks.size() == 0 && goldPath==null) {
                    expandTargets = brain.getAllNewWalkables();
                    state = "expand";
                    tmpUnreachableResources = new HashSet<>();
                }

                // Generate expansion movement tasks using expansion tasks.
                movePositionTasks = expandMoves(movePositionTasks, brain, goldPath, state, expandTargets);

                // Generate collection movement tasks using collection tasks.
                movePositionTasks = collectMoves(movePositionTasks, brain, goldPath, state, collectTargets, tmpUnreachableResources);

                //if movement task is non empty, execute the move.
                if (movePositionTasks.size() > 0) {
                    action = brain.moveCommand(movePositionTasks);
                    out.write(action);
                }else{ // no action in this round because of no path, skip it and change state.
                    action = 'n';
                }

                last_mapsize = brain.map.size(); //computing the map size when it reaches
            }

        } catch (IOException e) {
            System.out.println("Lost connection to port: " + port);
            System.exit(-1);
        } finally {
            try {
                socket.close();
            } catch (IOException e) {
            }
        }

    }

    /**
     * Generate collection move targets by searching resources on map, search path for each of them and command agent to collect by
     * returning movePositionTasks.
     * @param movePositionTasks
     * @param brain
     * @param goldPath
     * @param state
     * @param collectTargets
     * @param tmpUnreachableResources
     * @return
     */
    private static List<Position> collectMoves(List<Position> movePositionTasks, Brain brain, SearchState goldPath, String state, ArrayList<Position> collectTargets, Set<String> tmpUnreachableResources) {
        if (state.equals("collect")&&goldPath==null) {
            if (movePositionTasks.size() == 0) {
                for (int index = 0; index < collectTargets.size(); index++) {
                    Position target = collectTargets.remove(0); // next collection target
                    SearchState path = brain.search(brain.position.x, brain.position.y, target.x, target.y, false);
                    if (path != null) {
                        movePositionTasks = path.historyPosition;
                        movePositionTasks.remove(0);// remove the current position
                        break;
                    }else {
                        tmpUnreachableResources.add(Position.getPositionString(target.x,target.y));
                    }
                }

            }
        }
        return movePositionTasks;
    }

    /**
     * Generate expansion move targets by searching resources on map, search path for each of them and command agent to collect by
     * returning movePositionTasks.
     * @param movePositionTasks
     * @param brain
     * @param goldPath
     * @param state
     * @param expandTargets
     * @return
     */
    private static List<Position> expandMoves(List<Position> movePositionTasks, Brain brain, SearchState goldPath, String state, ArrayList<Position> expandTargets) {
        if (state.equals("expand") && goldPath==null ) {
            if (movePositionTasks.size() == 0) {
                for (int index = 0; index < expandTargets.size(); index++) {
                    Position target =  expandTargets.remove(0);
                    if (!brain.visited.contains(Position.getPositionString(target.x, target.y))) {
                        SearchState path = brain.search(brain.position.x, brain.position.y, target.x, target.y, false);
                        if (path != null) {
                            movePositionTasks = path.historyPosition;
                            movePositionTasks.remove(0);// remove the current position
                            break;
                        }
                    }
                }
            }
        }
        return movePositionTasks;
    }

    /**
     * original methond for receiving Stepping's 5*5 window.
     * @param in
     * @param view
     * @throws IOException
     */
    private static void scanView(InputStream in, char[][] view) throws IOException {
        int i;
        int j;
        int ch;
        for (i = 0; i < 5; i++) {

            for (j = 0; j < 5; j++) {
                if (!((i == 2) && (j == 2))) {
                    ch = in.read();
                    if (ch == -1) {
                        System.out.println("Game Won");
                        System.exit(-1);
                    }
                    view[i][j] = (char) ch;
                }
            }
        }
    }

    /**
     * Find visible resources and put them into respective lists
     * @param movePositionTasks
     * @param brain
     * @param goldPath
     * @param state
     * @param expandTargets
     * @param collectTargets
     * @param tmpUnreachableResources
     * @return
     */
    private static String getCollectTargets(List<Position> movePositionTasks,
                                            Brain brain, SearchState goldPath, String state,
                                            ArrayList<Position> expandTargets,
                                            ArrayList<Position> collectTargets,Set<String> tmpUnreachableResources) {


        if (expandTargets.size() == 0 && movePositionTasks.size() == 0 && goldPath==null) { // no expansion
            state = "collect";

            //collect stone keys and axes
            if (brain.keyPositions.size() > 0) {
                if (!brain.hasKey) {
                    for (Position keyP : brain.keyPositions) {
                        if (!collectTargets.contains(keyP) && !tmpUnreachableResources.contains
                                (Position.getPositionString(keyP.x,keyP.y))) {
                            collectTargets.add(keyP);
                        }
                    }
                }
            }

            if (brain.axePositions.size() > 0) {
                if (!brain.hasAxe) {
                    for (Position axeP : brain.axePositions) {

                        if (!collectTargets.contains(axeP)&& !tmpUnreachableResources.contains
                                (Position.getPositionString(axeP.x,axeP.y))) {
                            collectTargets.add(axeP);

                        }
                    }
                }
            }

            if (brain.stonesPositions.size() > 0) {
                for (Position stoneP : brain.stonesPositions) {
                    if (!collectTargets.contains(stoneP)&&!tmpUnreachableResources.contains
                            (Position.getPositionString(stoneP.x,stoneP.y))) {
                        collectTargets.add(stoneP);
                    }
                }

            }
        }

        return state;
    }
}


class Brain {

    public HashMap<String, Character> map = new HashMap<>(); // the world map storing each possition in the world
    Set<Character> globalWalkable = new HashSet<>(); // the char set the an agent can walk onto
    Position position;// the agent's current position
    char direction;
    // the agent's facing direction, Regardless of actual global direction,
    // the "born" direction always is considered to be North.
    Position goldPosition = null;//gold's position when gold is found
    LinkedList<Position> keyPositions = new LinkedList<>(); // list of where keys are
    LinkedList<Position> axePositions = new LinkedList<>(); // list of where axes are
    LinkedList<Position> stonesPositions = new LinkedList<>();// list of where stones are

    Set<String> visited = new HashSet<>();
    // all visited position is in there so in
    // expansion does not try to search path of a visited position

    // the max boundary is the maximum boundary agent has explored,
    // not all position has been explored in this region confined by boundries
    int south_boundary = 0;
    int north_boundary = 0;
    int west_boundary = 0;
    int east_boundary = 0;

    boolean hasAxe = false;
    boolean hasKey = false;
    boolean goldOnHand = false;
    int numberOfStone = 0;

    public Brain(char[][] view) throws IOException { //initialize parameters for agent and store 5*5 initial map.
        //initialize map by adding the first view
        globalWalkable.addAll(Arrays.asList((new Character[]{' ', 'a', 'g', 'k', 'o', 'O'})));
        direction = 'N';
        this.position = new Position(0, 0);
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                int x = j - 2;
                int y = 2 - i;
                updateResourcePosition(x, y, view[i][j]);
                if (!((i == 2) && (j == 2))) {
                    map.put(Position.getPositionString(x, y), view[i][j]);
                } else {//the start point
                    map.put(Position.getPositionString(x, y), ' ');
                    visited.add(Position.getPositionString(x, y));
                }
            }
        }

        // the initial boundary 5*5 square, marks the boundary of map
        this.south_boundary = -2; //boundary
        this.north_boundary = 2;
        this.east_boundary = 2;
        this.west_boundary = -2;

//        System.out.print(map.size());
//        System.out.println("stored Map:");
//        this.printMap();
//        System.out.println();
    }

    //return whether stone is in sight
    public boolean stoneInSight() {
        return map.containsKey('o');
    }
    //return whether key is in sight
    public boolean keyInSight() {
        return map.containsKey('k');
    }


    /**
     * update the map when agent go south
     * @param view
     */
    private void updateNorth(char[][] view) {
        position.y += 1;//1
        upDateHoldingResources(position.x, position.y);//2
        removeResources();//3
        visited.add(Position.getPositionString(position.x, position.y));//4

        int new_north_boundary = position.y + 2;
        //update the boundary of this map
        if (new_north_boundary > north_boundary) {
            this.north_boundary = new_north_boundary;
        }
        //update upto 5 point
        for (int i = -2; i <= 2; i++) {
            //horizontal:
            int x = position.x + i;
            int y = position.y + 2;
            updateResourcePosition(x, y, view[0][i + 2]);
            map.put(Position.getPositionString(x, y), view[0][i + 2]);

        }


    }

    /**
     * update the map when agent go south
     *
     * @param view
     */
    private void updateSouth(char[][] view) {
        position.y -= 1;//1
        upDateHoldingResources(position.x, position.y);//2
        removeResources();//3
        visited.add(Position.getPositionString(position.x, position.y));//4
        int new_south_boundary = position.y - 2;
        if (new_south_boundary < south_boundary) {
            this.south_boundary = new_south_boundary;
        }

        for (int i = -2; i <= 2; i++) {
            int x = position.x + i;
            int y = position.y - 2;
            map.put(Position.getPositionString(x, y), view[0][2 - i]);
            updateResourcePosition(x, y, view[0][2 - i]);
        }


    }

    /**
     * update the map when agent go South
     *
     * @param view
     */
    private void updateEast(char[][] view) {
        position.x += 1; //1
        upDateHoldingResources(position.x, position.y);//2
        removeResources();//3
        visited.add(Position.getPositionString(position.x, position.y));//4

        int new_east_boundary = position.x + 2;
        if (east_boundary < new_east_boundary) {
            this.east_boundary = new_east_boundary;
        }

        for (int j = 2; j >= -2; j--) {
            int x = position.x + 2;
            int y = position.y + j;
            updateResourcePosition(x, y, view[0][2 - j]);
            map.put(Position.getPositionString(x, y), view[0][2 - j]);
        }


    }

    /**
     * update the map when agent go West
     *
     * @param view
     */
    private void updateWest(char[][] view) {
        position.x -= 1; // 1
        upDateHoldingResources(position.x, position.y); //2
        removeResources(); //3
        visited.add(Position.getPositionString(position.x, position.y));//4

        int new_west_boundary = position.x - 2;
        if (new_west_boundary < west_boundary) {
            west_boundary = new_west_boundary;
        }

        for (int j = -2; j <= 2; j++) {
            int x = position.x - 2;
            int y = position.y + j;
            updateResourcePosition(x, y, view[0][2 + j]);
            map.put(Position.getPositionString(x, y), view[0][2 + j]);
        }


    }


    private void upDateHoldingResources(int x,int y){
        if(map.get(Position.getPositionString(x,y)) == 'k'){
            this.hasKey = true;
            globalWalkable.add('-');
        }

        if(map.get(Position.getPositionString(x,y)) == 'a'){
            this.hasAxe = true;
            globalWalkable.add('T');
        }

        if(map.get(Position.getPositionString(x,y))=='o'){
            this.numberOfStone+=1;
        }

        if(map.get(Position.getPositionString(x,y))=='g'){
            goldOnHand = true;
        }

    }

    private void removeResources() {
        if (map.get(Position.getPositionString(position.x, position.y)) == 'k') {
            map.put(Position.getPositionString(position.x, position.y), ' ');
            removeResourceList(position.x, position.y, this.keyPositions);
        }

        if (map.get(Position.getPositionString(position.x, position.y)) == 'o') {
            map.put(Position.getPositionString(position.x, position.y), ' ');
            removeResourceList(position.x, position.y, this.stonesPositions);
        }

        if (map.get(Position.getPositionString(position.x, position.y)) == 'a') {
            map.put(Position.getPositionString(position.x, position.y), ' ');
            removeResourceList(position.x, position.y, this.axePositions);
        }
    }


    private void removeResourceList(int re_x, int re_y, LinkedList<Position> list) {

        for (Position position : list) {
            if (position.x == re_x && position.y == re_y) {
                list.remove(position);
                break;
            }

        }

    }


    private void updateResourcePosition(int x, int y, char resource) {
        if (resource == 'g') {
            this.goldPosition = new Position(x, y);
        }

        if (resource == 'a') {
            if (!repeatResoruceCheck(x, y, axePositions)) {
                axePositions.add(new Position(x, y));
            }
        }

        if (resource == 'k') {
            if (!repeatResoruceCheck(x, y, keyPositions)) {
                keyPositions.add(new Position(x, y));
            }


        }

        if (resource == 'o') {
            if (!repeatResoruceCheck(x, y, stonesPositions)) {
                stonesPositions.add(new Position(x, y));
            }

        }

    }

    //check if new view detect resource, check if it is an old, stored position
    private boolean repeatResoruceCheck(int x, int y, List<Position> positions) {

        for (Position p : positions) {
            if (p.x == x && p.y == y) {
                return true;
            }
        }

        return false;

    }

    /**
     * print the map every time agent make a F move, only use in test
     */
    public void printMap() {
        System.out.println();

        int h_border = east_boundary - west_boundary + 1;
        //print up border
        System.out.print("+");
        for (int x = 0; x < h_border; x++) {
            System.out.print("-");
        }
        System.out.println("+");


        for (int i = this.north_boundary; i >= this.south_boundary; i--) {
            System.out.print("|");
            for (int j = this.west_boundary; j <= this.east_boundary; j++) {
                if (map.containsKey(Position.getPositionString(j, i))) {
                    if (position.x == j && position.y == i) {
                        System.out.print('@');
                    } else {
                        System.out.print(map.get(Position.getPositionString(j, i)));
                    }

                } else {
                    System.out.print('X');
                }
            }
            System.out.println("|");
        }
        //bottom border
        System.out.print("+");
        for (int x = 0; x < h_border; x++) {
            System.out.print("-");
        }
        System.out.println("+");
    }


    /**
     * change direction when turn right
     */
    private void turnRight() {
        switch (direction) {
            case 'N':
                this.direction = 'E';
                break;
            case 'E':
                this.direction = 'S';
                break;
            case 'S':
                this.direction = 'W';
                break;
            case 'W':
                this.direction = 'N';

        }
    }

    /**
     * change direction when turn left
     */
    private void turnLeft() {

        switch (direction) {
            case 'N':
                this.direction = 'W';
                break;
            case 'W':
                this.direction = 'S';
                break;
            case 'S':
                this.direction = 'E';
                break;
            case 'E':
                this.direction = 'N';

        }

    }

    /**
     * update agent's map or direction based on its move
     * @param action
     * @param view
     */
    public void worldAction(char action, char[][] view) {
        if (action == 'R' || action == 'r') {
            turnRight();
        } else if (action == 'L' || action == 'l') {
            turnLeft();
        } else if (action == 'F' || action == 'f') {
            switch (this.direction) {
                case 'N':
                    this.updateNorth(view);
                    break;
                case 'S':
                    this.updateSouth(view);
                    break;
                case 'E':
                    this.updateEast(view);
                    break;
                case 'W':
                    this.updateWest(view);
                    break;

            }
        }

//        System.out.println();
//        this.printMap();

    }


    /**
     * In exploration state, determine whether a position is walkable
     * Does not consider '~' in this state since ~ is only considered walkable when gold is found and it is used in the
     * search map not the actual map.
     *
     * @param x
     * @param y
     * @param copiedMap
     * @return
     */
    private boolean isWalkable(int x, int y, final HashMap<String, Character> copiedMap) {
        if (copiedMap.containsKey(Position.getPositionString(x, y))) {
            if (globalWalkable.contains(copiedMap.get(Position.getPositionString(x, y)))) {
                return true;
            }
        }
        return false;
    }


    /**
     * Get the north of current coordinate
     *
     * @param x current x coordinate
     * @param y current y coordinate
     * @return the north of current coordinate int [0] = x int[1] = y
     */
    private int[] getNorthCoordinate(int x, int y) {
        int[] corrdinate = new int[2];
        int new_y = y + 1;
        corrdinate[0] = x;
        corrdinate[1] = new_y;
        return corrdinate;

    }

    /**
     * Get the South of current coordinate
     *
     * @param x current x coordinate
     * @param y current y coordinate
     * @return the south of current coordinate int [0] = x int[1] = y
     */
    private int[] getSouthCoordinate(int x, int y) {
        int[] corrdinate = new int[2];
        int new_y = y - 1;
        corrdinate[0] = x;
        corrdinate[1] = new_y;
        return corrdinate;

    }

    /**
     * Get the East of current coordinate
     *
     * @param x current x coordinate
     * @param y current y coordinate
     * @return the east of current coordinate int [0] = x int[1] = y
     */
    private int[] getEastCoordinate(int x, int y) {
        int[] corrdinate = new int[2];
        int new_x = x + 1;
        corrdinate[0] = new_x;
        corrdinate[1] = y;
        return corrdinate;

    }

    /**
     * Get the West of current coordinate
     *
     * @param x current x coordinate
     * @param y current y coordinate
     * @return the west of current coordinate int [0] = x int[1] = y
     */
    private int[] getWestCoordinate(int x, int y) {
        int[] corrdinate = new int[2];
        int new_x = x - 1;
        corrdinate[0] = new_x;
        corrdinate[1] = y;
        return corrdinate;
    }

    /**
     * A* search path algorithm, computing an optimal Path contained in the last position object.
     *
     * @param goal_x
     * @param goal_y
     * @param start_x
     * @param start_y
     * @return
     */

    /**
     * determine the next move based on the command
     *
     * @param path
     * @return
     */
    public char moveCommand(List<Position> path) {

        Position nextPosition = path.get(0);

        if (position.x - nextPosition.x == 1) { // next position is to the west of the agent
            if (direction == 'W') {
                Character x = useResource(nextPosition);
                if (x != null) return x;
                path.remove(0);
                return 'F';
            } else {
                if (direction == 'N') return 'L';
                if (direction == 'S') return 'R';
                if (direction == 'E') return 'L';
            }
        }


        if (nextPosition.x - position.x == 1) { // next position is to the east of the agent
            if (direction == 'E') {
                Character x = useResource(nextPosition);
                if (x != null) return x;
                path.remove(0);
                return 'F';
            } else {
                if (direction == 'N') return 'R';
                if (direction == 'S') return 'L';
                if (direction == 'W') return 'L';
            }
        }

        if (nextPosition.y - position.y == 1) { // next position is to the north of the agent
            if (direction == 'N') {
                Character x = useResource(nextPosition);
                if (x != null) return x;
                path.remove(0);
                return 'F';
            } else {
                if (direction == 'W') return 'R';
                if (direction == 'E') return 'L';
                if (direction == 'S') return 'L';
            }
        }


        if (position.y - nextPosition.y == 1) { // next position is to the south of the agent
            if (direction == 'S') {
                Character x = useResource(nextPosition);
                if (x != null) return x;
                path.remove(0);
                return 'F';
            } else {
                if (direction == 'W') return 'L';
                if (direction == 'E') return 'R';
                if (direction == 'N') return 'L';
            }
        }

        return ' ';
    }

    private Character useResource(Position nextPosition) {
        if(map.get(Position.getPositionString(nextPosition.x,nextPosition.y)) == 'T'){
            map.put(Position.getPositionString(nextPosition.x,nextPosition.y),' ');
            return 'C';
        }else if(map.get(Position.getPositionString(nextPosition.x,nextPosition.y))=='-'){
            map.put(Position.getPositionString(nextPosition.x,nextPosition.y),' ');
            return 'U';
        }else if(map.get(Position.getPositionString(nextPosition.x,nextPosition.y))=='~'){
            map.put(Position.getPositionString(nextPosition.x,nextPosition.y),' ');
            this.numberOfStone-=1;
        }

        return null;
    }

    /**
     * Get all unwalked position in current map, sort it based on the proximity to the current position
     * in decreasing order so that the agent can visit futher position first then some near position can be
     * removed from wish walk list
     *
     * @return
     */
    public ArrayList<Position> getAllNewWalkables() {
        ArrayList<Position> allNewWalables = new ArrayList<>();


        for (int y = this.south_boundary; y <= this.north_boundary; y++) {
            for (int x = this.west_boundary; x <= this.east_boundary; x++) {
                if (this.isWalkable(x, y, map) && !visited.contains(Position.getPositionString(x, y))) {
                    allNewWalables.add(new Position(x, y));
                }
            }
        }

//        Collections.sort(allNewWalables, new Comparator<Position>() {
//            @Override
//            public int compare(Position p1, Position p2) {
//                if (Brain.shortestDistance(position.x, position.y, p1.x, p1.y) <
//                        Brain.shortestDistance(position.x, position.y, p2.x, p2.y)) {
//                    return 1;
//                }
//
//                if (Brain.shortestDistance(position.x, position.y, p1.x, p1.y) >
//                        Brain.shortestDistance(position.x, position.y, p2.x, p2.y)) {
//                    return -1;
//                }
//                return 0;
//            }
//        });

        return allNewWalables;
    }

    /**
     * conpute the shortest distance between two position
     */
    public static double shortestDistance(int x, int y, int g_x, int g_y) {

        return Math.abs(g_x - x) + Math.abs(g_y - y);

    }

    /**
     * The evaluation function in A* search, which is shortestDistance+currentMoveCount
     */
    public static double stateEvaluationFunction(SearchState state, int g_x, int g_y) {
        return state.historyPosition.size() + shortestDistance(state.position.x, state.position.y, g_x, g_y);
    }

    /**
     * The A* search function, searching a path using start position and goal position
     * @param start_x the x position of start
     * @param start_y the y position of start
     * @param goal_x the x position of goal
     * @param goal_y the y position of goal
     * @param goldPathSearch if it is goal search, consider ~ otherwise not
     * @return
     */
    public SearchState search(int start_x, int start_y, final int goal_x, final int goal_y, boolean goldPathSearch) {
        Set<String> expandedSet = new HashSet<>();
        PriorityQueue<SearchState> priorityQueue = new PriorityQueue<> (100,new MyComparator(goal_x,goal_y));
        Stack<Position> historymove = new Stack<>();
        SearchState startState = new SearchState(start_x, start_y,
                this.hasAxe, this.hasKey, this.numberOfStone,historymove, (HashMap<String, Character>) map.clone());
        priorityQueue.add(startState);
        while (!priorityQueue.isEmpty()) {
            SearchState curState = priorityQueue.remove();
            expandedSet.add(curState.getstateID());
            if (curState.position.x == goal_x && curState.position.y == goal_y) {
                curState.historyPosition.push(curState.position);
                return curState;
            }

            //Initialize walkableMark for this State if it has tool, add new mark respectively
            Set<Character> walkableMark = new HashSet<>();
            walkableMark.addAll(Arrays.asList((new Character[]{' ', 'a', 'g', 'k', 'o', 'O'})));
            if (curState.hasKey) {
                walkableMark.add('-');
            }

            if (curState.hasAxe) {
                walkableMark.add('T');
            }

            for (int i = 0; i < 4; i++) { //expand towards north, east, south, west respectively
                int[] next = null;

                if (i == 0) {
                    next = this.getNorthCoordinate(curState.position.x, curState.position.y);
                } else if (i == 1) {
                    next = this.getEastCoordinate(curState.position.x, curState.position.y);
                } else if (i == 2) {
                    next = this.getSouthCoordinate(curState.position.x, curState.position.y);
                }else if (i == 3) {
                    next = this.getWestCoordinate(curState.position.x, curState.position.y);
                }
                //check if the position is inside the map
                if (curState.privateMap.containsKey(Position.getPositionString(next[0], next[1]))) {
                    char nextValue = curState.privateMap.get(Position.getPositionString(next[0], next[1]));
                    if (walkableMark.contains(nextValue)) {
                        boolean nextHasAxe;
                        boolean nextHasKey;
                        int next_num_of_stone;

                        if (nextValue == 'a') {
                            nextHasAxe = true;
                        } else {
                            nextHasAxe = curState.hasAxe;
                        }

                        if (nextValue == 'o') {
                            next_num_of_stone = curState.num_of_stone + 1;
                        } else {
                            next_num_of_stone = curState.num_of_stone;
                        }

                        if (nextValue == 'k') {
                            nextHasKey = true;
                        } else {
                            nextHasKey = curState.hasKey;
                        }

                        HashMap<String, Character> newMap = (HashMap<String, Character>) curState.privateMap.clone();

                        newMap.put(Position.getPositionString(next[0], next[1]), ' ');
                        Stack<Position> pathHistory = (Stack<Position>) curState.historyPosition.clone();
                        pathHistory.push(curState.position);
                        SearchState nextState = new SearchState(next[0], next[1], nextHasAxe, nextHasKey,
                                next_num_of_stone, pathHistory, newMap);
                        if (!expandedSet.contains(nextState.getstateID())) {
                            priorityQueue.add(nextState);
                        }

                    } else if (nextValue == '~' && goldPathSearch && curState.num_of_stone > 0) {
                        //decide to move onto water by using one stone as long as gold in map.
                        HashMap<String, Character> newMap = (HashMap<String, Character>) curState.privateMap.clone();
                        newMap.put(Position.getPositionString(next[0], next[1]), 'O');
                        Stack<Position> pathHistory = (Stack<Position>) curState.historyPosition.clone();
                        pathHistory.push(curState.position);
                        SearchState nextState = new SearchState(next[0], next[1], curState.hasAxe, curState.hasKey,
                                curState.num_of_stone - 1, pathHistory, newMap);

                        if (!expandedSet.contains(nextState.getstateID())) {
                            priorityQueue.add(nextState);
                        }
                    }
                }
            }
        }
        return null;
    }



}


class Position { // simple position class stores coordinates

    int x;
    int y;

    public Position(int x, int y) {
        this.x = x;
        this.y = y;
    }

    public static String getPositionString(int x, int y) {
        return x + "," + y;
    }


    @Override
    public String toString() {
        return "(" + x + "," + y + ")";
    }

}

/**
 * The search state in path search, containing a series of identifier to help it distinguishes with other states.
 */
class SearchState {

    Position position;
    Boolean hasKey = false;
    Boolean hasAxe = false;
    Integer num_of_stone = 0;
    Stack<Position> historyPosition;
    HashMap<String, Character> privateMap; // each search state has its own map since it might alter it

    public SearchState(int x, int y, boolean hasAxe, boolean hasKey,
                       int num_of_stone, Stack<Position> historyPosition, HashMap<String, Character> privateMap) {
        position = new Position(x, y);
        this.hasAxe = hasAxe;
        this.hasKey = hasKey;
        this.num_of_stone = num_of_stone;
        this.historyPosition = historyPosition;
        this.privateMap = privateMap;
    }

    /**
     * Generate state ID in a search to help hash set find any repeat state
     * @return
     */
    public String getstateID() {
        return Integer.toString(this.position.x) + "," + Integer.toString(this.position.y)
                + "," + Boolean.toString(hasKey) + "," + Boolean.toString(hasAxe) + "," +
                Integer.toString(num_of_stone)+","+this.privateMap.get(Position.getPositionString(position.x,position.y+1))+
                this.privateMap.get(Position.getPositionString(position.x+1,position.y))+
                this.privateMap.get(Position.getPositionString(position.x-1,position.y))+
                this.privateMap.get(Position.getPositionString(position.x,position.y-1));
    }




}


class MyComparator implements Comparator<SearchState>{

    int goal_x;
    int goal_y;

    public MyComparator(int goal_x, int goal_y){
        this.goal_x = goal_x;
        this.goal_y = goal_y;

    }

    @Override
    public int compare(SearchState s1, SearchState s2) {

        if (Brain.stateEvaluationFunction(s1, goal_x, goal_y)
                < Brain.stateEvaluationFunction(s2, goal_x, goal_y)) {
            return -1;
        }

        if (Brain.stateEvaluationFunction(s1, goal_x, goal_y)
                > Brain.stateEvaluationFunction(s2, goal_x, goal_y)) {
            return 1;
        }

        return 0;
    }
}




