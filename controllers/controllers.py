#-*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class OA(http.Controller):
    @http.route('/oa/oa/', auth='public')
    def index(self, **kw):
        return "Hello, world"

   # @http.route('/oa/oa/courses/', type='http', auth='public', website=True)
    @http.route([
        '''/courses''',
        '''/courses/page/<int:page>'''
    ], type='http', auth='public', website=True)
    def course(self, page=0 , search=''):
        domain = [('is_course','=',True)]		

        if search:
            domain = [('name', 'ilike' ,search)]

        total_courses = request.env['product.template'].search(domain)
        course_count = len(total_courses)
        
        logging.info("courses %s" , total_courses)
        ppg = 3

        pager = request.website.pager(url='/courses', total=course_count, page=page, step=ppg, scope=3, url_args=None)
        courses =  request.env['product.template'].sudo().search(domain, limit=ppg, offset=pager['offset'], order='id asc')

        for c in courses:
            if c:
                if c.image_1920:
                     logging.info("c.image_1920");
                else:
                     logging.info("c.image_1920 not found");
            else:
                logging.info(" C absent!!")
        for c in courses:
            if c:
                if c.image_128:
                     logging.info("c.image_128");
                else:
                     logging.info("c.image_128 not found");
            else:
                logging.info(" C2 absent!!")


 
              
        values = {
            'courses':courses,
            'pager': pager,   
        }  
        return http.request.render('oa.course', values)


#     @http.route('/check_scaff/check_scaff/objects/<model("check_scaff.check_scaff"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('check_scaff.object', {
#             'object': obj
#         })

    @http.route('/courses/details/<int:course_id>/', auth='public', website=True)
 #   @http.route(['/courses/details/<model("product.template"):course>'], type='http', auth='public' , website=True)
    def course_details(self,course_id):
        logging.info ("Incoming Course Id %s " , course_id)
        domain = [('id','=',course_id)]
        logging.info ("Domain :   %s " , domain)

        course_det = request.env['product.template'].sudo().search(domain)
	
        logging.info ("Course Det  %s " , course_det.level)
        logging.info ("Course Det  %s " , course_det.session_ids)
        logging.info ("Course  : %s " , course_det)

        values = {'course':course_det}
        return request.render("oa.course_details", values)   


#    @http.route(['/session/details/<model("oa.session"):session>'], type='http', auth='public' , website=True)
#    def session_details(self,session):
#       values = {'session':session}

#       return request.render("oa.session_details", values)   


    @http.route(['/session/details/<int:session_id>'], type='http', auth='public' , website=True)
    def session_details(self,session_id):
        logging.info ("Session Incoming :  %s " , session_id) 
        domain = [('id','=',session_id)]
        logging.info (" Domain :  %s " , session_id)

        session = request.env['oa.session'].sudo().search(domain)
        values = {'session' : session}

        return request.render("oa.session_details", values)   

