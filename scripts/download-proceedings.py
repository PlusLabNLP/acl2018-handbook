import os
import shutil

output_dir = "data"

with open('../input/conferences.txt') as f:
    content = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content = [x.strip() for x in content] 

for c in content:
    url = "http://www.softconf.com/acl2020/"+c+"/pub/aclpub/proceedings.tgz"
    directory = "../" + output_dir + "/"+c
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.system("curl \""+url+"\" > "+directory+"/proceedings.tgz")
    os.system("tar -zx -C "+directory+" -f "+directory+"/proceedings.tgz" + \
        " proceedings/meta proceedings/order proceedings/final.tgz")
    os.system("tar -zx -C " + directory + "/proceedings" + " -f " + directory + "/proceedings/final.tgz")
    os.rename(directory+"/proceedings/final", directory+"/final")
    os.rename(directory+"/proceedings/order", directory+"/order")
    os.rename(directory+"/proceedings/meta", directory+"/meta")
    os.remove(directory+"/proceedings.tgz")
    shutil.rmtree(directory+"/proceedings")
