package no.ntnu.nav.getDeviceData.plugins;

import java.util.*;

public class DeviceData
{
	String sysname;

	//List propertyList;
	List boksDisk = new ArrayList();
	boolean boksDiskUpdated;
	List boksInterface = new ArrayList();
	boolean boksInterfaceUpdated;

	public DeviceData() {

	}

	/**
	 * Set the sysname; if it is not blank the database will be updated if needed
	 *
	 * @param s the new sysname for this boks
	 */
	public void setSysname(String s) { sysname = s; }

	public String getSysname() { return sysname; }

	/**
	 * Add this path to the boks; any news paths will be inserted into the database, paths
	 * in the database not added here will be removed.
	 *
	 * @param path The path to add
	 */
	public void addBoksDisk(String path) { if (path != null) boksDisk.add(path); }

	/**
	 * Call this method to enable updating of boksdisk. NOTE: If you call this method but
	 * don't add any paths all paths in the database for this boks will be deleted.
	 */
	public void boksDiskUpdated() { boksDiskUpdated = true; }

	public List getBoksDisk() { return boksDisk; }
	public boolean getBoksDiskUpdated() { return boksDiskUpdated; }

	/**
	 * Add this interface to the boks; any news interfaces will be inserted into the database, interfacess
	 * in the database not added here will be removed.
	 *
	 * @param interf The interface to add
	 */
	public void addBoksInterface(String interf) { if (interf != null) boksInterface.add(interf); }

	/**
	 * Call this method to enable updating of boksinterface. NOTE: If you call this method but
	 * don't add any interfaces all interfaces in the database for this boks will be deleted.
	 */
	public void boksInterfaceUpdated() { boksInterfaceUpdated = true; }

	public List getBoksInterface() { return boksInterface; }
	public boolean getBoksInterfaceUpdated() { return boksInterfaceUpdated; }





}