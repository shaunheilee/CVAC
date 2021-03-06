package cvac.fileserver;

import cvac.FileService;

/**
 * The start and stop mechanisms for a FileService:
 * it can be started either in an IceBox or standalone.
 *
 * @author matz
 */
public class FileServer extends Ice.Application 
{
    @Override
    public int run(String[] args)
    {
        System.out.println("Started FileServer with arguments: " + args);
        
        FileService fs = new FileServiceI();

        // this starts the actual service
        Ice.Communicator ic = communicator();
        Ice.ObjectAdapter adapter =
            ic.createObjectAdapterWithEndpoints("FileServiceAdapter", "default -p 10110");
        adapter.add( fs, ic.stringToIdentity("FileService") );
        ic.getProperties().setProperty( "CVAC.DataDir", "data" );
        adapter.activate();

        // now just wait for a shutdown signal
        ic.waitForShutdown();
        return 0;
    }

    /**
     * Start this as follows, with the paths to the jar files changed according
     * to your file structure:
     * java -cp "./lib/FileServer.jar:./3rdparty/ICE/lib/Ice.jar" cvac.fileserver.FileServer
     * 
     * @param args 
     */
    public static void main(String[] args)
    {
        FileServer app = new FileServer();
        // int status = app.main("FileServer", args, "config.service");
        int status = app.main("FileServer", args);
        System.exit(status);
    }
}
